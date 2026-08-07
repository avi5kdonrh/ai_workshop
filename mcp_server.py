#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JAEGER_BASE_URL = "http://localhost:16686"

mcp = FastMCP("HTTP Endpoint MCP Server")


def _get_tag(span: dict, key: str, default=None):
    for tag in span.get("tags", []):
        if tag["key"] == key:
            return tag["value"]
    return default


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[f]
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


async def _fetch_traces(
    client: httpx.AsyncClient, service: str, jaeger_url: str,
    lookback: str, limit: int,
) -> list[dict]:
    resp = await client.get(
        f"{jaeger_url}/api/traces",
        params={"service": service, "lookback": lookback, "limit": str(limit)},
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


@mcp.tool()
async def get_service_health(
    service: str,
    lookback: str = "1h",
    limit: int = 500,
    jaeger_url: str = JAEGER_BASE_URL,
) -> dict:
    """
    Get an aggregated health summary for a service from Jaeger traces.
    Processes traces server-side and returns compact metrics instead of raw data.

    Args:
        service: Service name in Jaeger (default: store-service)
        lookback: Time window to look back (e.g. 1h, 30m, 2h, 1d)
        limit: Max number of traces to fetch for analysis (default: 500)
        jaeger_url: Jaeger base URL (default: http://localhost:16686)

    Returns:
        Health summary with throughput, error rate, latency percentiles,
        per-operation breakdown, and top errors.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            traces = await _fetch_traces(client, service, jaeger_url, lookback, limit)
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch traces: {e}"}

    if not traces:
        return {
            "service": service,
            "lookback": lookback,
            "status": "NO_DATA",
            "message": "No traces found for this service in the given time window.",
        }

    all_spans = []
    root_spans = []
    for trace in traces:
        spans = trace.get("spans", [])
        all_spans.extend(spans)
        span_ids = {s["spanID"] for s in spans}
        for span in spans:
            refs = span.get("references", [])
            parent_ids = {r["spanID"] for r in refs if r.get("refType") == "CHILD_OF"}
            if not parent_ids or not parent_ids.intersection(span_ids):
                root_spans.append(span)

    op_stats = defaultdict(lambda: {
        "count": 0, "errors": 0, "durations_us": [],
        "status_codes": defaultdict(int),
    })

    total_errors = 0
    error_details = []

    for span in all_spans:
        op = span["operationName"]
        dur = span.get("duration", 0)
        stats = op_stats[op]
        stats["count"] += 1
        stats["durations_us"].append(dur)

        status_code = _get_tag(span, "http.response.status_code")
        if status_code is not None:
            stats["status_codes"][int(status_code)] += 1

        is_error = (
            _get_tag(span, "error") is True
            or _get_tag(span, "otel.status_code") == "ERROR"
            or (status_code is not None and int(status_code) >= 400)
        )
        if is_error:
            stats["errors"] += 1
            total_errors += 1
            if len(error_details) < 10:
                error_details.append({
                    "operation": op,
                    "status_code": int(status_code) if status_code else None,
                    "duration_ms": round(dur / 1000, 2),
                    "error_message": _get_tag(span, "otel.status_description", ""),
                    "url_path": _get_tag(span, "url.path", ""),
                })

    root_durations = sorted([s.get("duration", 0) for s in root_spans])

    operations = []
    for op, stats in sorted(op_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        durs = sorted(stats["durations_us"])
        op_summary = {
            "operation": op,
            "count": stats["count"],
            "error_count": stats["errors"],
            "error_rate_pct": round(stats["errors"] / stats["count"] * 100, 1) if stats["count"] else 0,
            "latency_ms": {
                "avg": round(sum(durs) / len(durs) / 1000, 2) if durs else 0,
                "p50": round(_percentile(durs, 50) / 1000, 2),
                "p95": round(_percentile(durs, 95) / 1000, 2),
                "p99": round(_percentile(durs, 99) / 1000, 2),
                "max": round(max(durs) / 1000, 2) if durs else 0,
            },
        }
        if stats["status_codes"]:
            op_summary["status_codes"] = dict(stats["status_codes"])
        operations.append(op_summary)

    overall_error_rate = round(total_errors / len(all_spans) * 100, 1) if all_spans else 0

    if overall_error_rate > 10:
        health = "CRITICAL"
    elif overall_error_rate > 5:
        health = "DEGRADED"
    elif overall_error_rate > 0:
        health = "WARNING"
    else:
        health = "HEALTHY"

    return {
        "service": service,
        "lookback": lookback,
        "health": health,
        "summary": {
            "trace_count": len(traces),
            "total_spans": len(all_spans),
            "total_errors": total_errors,
            "error_rate_pct": overall_error_rate,
        },
        "end_to_end_latency_ms": {
            "avg": round(sum(root_durations) / len(root_durations) / 1000, 2) if root_durations else 0,
            "p50": round(_percentile(root_durations, 50) / 1000, 2),
            "p95": round(_percentile(root_durations, 95) / 1000, 2),
            "p99": round(_percentile(root_durations, 99) / 1000, 2),
            "max": round(max(root_durations) / 1000, 2) if root_durations else 0,
        },
        "operations": operations,
        "recent_errors": error_details,
    }


@mcp.tool()
async def get_service_operations(
    service: str,
    jaeger_url: str = JAEGER_BASE_URL,
) -> dict:
    """
    List all known operations for a service from Jaeger.

    Args:
        service: Service name in Jaeger (default: store-service)
        jaeger_url: Jaeger base URL (default: http://localhost:16686)

    Returns:
        List of operation names for the service.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{jaeger_url}/api/services/{service}/operations")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch operations: {e}"}


@mcp.tool()
async def compare_service_health(
    service: str,
    current_window: str = "1h",
    previous_window: str = "2h",
    limit: int = 500,
    jaeger_url: str = JAEGER_BASE_URL,
) -> dict:
    """
    Compare current service health against a previous time window to detect regressions.

    Args:
        service: Service name in Jaeger (default: store-service)
        current_window: Recent time window (e.g. 1h)
        previous_window: Larger window that includes older data for comparison (e.g. 2h)
        limit: Max traces per window (default: 500)
        jaeger_url: Jaeger base URL (default: http://localhost:16686)

    Returns:
        Side-by-side comparison of error rates and latencies between the two windows,
        highlighting any regressions.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            current_traces = await _fetch_traces(client, service, jaeger_url, current_window, limit)
            all_traces = await _fetch_traces(client, service, jaeger_url, previous_window, limit)
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch traces: {e}"}

    current_trace_ids = {t["traceID"] for t in current_traces}
    previous_traces = [t for t in all_traces if t["traceID"] not in current_trace_ids]

    def _summarize(traces):
        if not traces:
            return {"trace_count": 0, "error_rate_pct": 0, "avg_latency_ms": 0, "p95_latency_ms": 0}
        spans = [s for t in traces for s in t.get("spans", [])]
        errors = sum(
            1 for s in spans
            if _get_tag(s, "error") is True
            or _get_tag(s, "otel.status_code") == "ERROR"
            or ((_sc := _get_tag(s, "http.response.status_code")) is not None and int(_sc) >= 400)
        )
        durations = sorted([s.get("duration", 0) for s in spans])
        return {
            "trace_count": len(traces),
            "span_count": len(spans),
            "error_count": errors,
            "error_rate_pct": round(errors / len(spans) * 100, 1) if spans else 0,
            "avg_latency_ms": round(sum(durations) / len(durations) / 1000, 2) if durations else 0,
            "p95_latency_ms": round(_percentile(durations, 95) / 1000, 2),
        }

    current_summary = _summarize(current_traces)
    previous_summary = _summarize(previous_traces)

    regressions = []
    if current_summary["error_rate_pct"] > previous_summary["error_rate_pct"] + 2:
        regressions.append(
            f"Error rate increased: {previous_summary['error_rate_pct']}% -> {current_summary['error_rate_pct']}%"
        )
    if previous_summary["p95_latency_ms"] > 0:
        latency_change = (
            (current_summary["p95_latency_ms"] - previous_summary["p95_latency_ms"])
            / previous_summary["p95_latency_ms"] * 100
        )
        if latency_change > 20:
            regressions.append(
                f"P95 latency increased by {latency_change:.0f}%: "
                f"{previous_summary['p95_latency_ms']}ms -> {current_summary['p95_latency_ms']}ms"
            )

    return {
        "service": service,
        "current_window": current_window,
        "previous_window": previous_window,
        "current": current_summary,
        "previous": previous_summary,
        "regressions": regressions if regressions else ["No regressions detected"],
    }


def _find_pid_by_name(process_name: str) -> str:
    result = subprocess.run(
        ["jps", "-l"], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"jps failed: {result.stderr.strip()}")
    for line in result.stdout.strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and process_name in parts[1]:
            return parts[0]
    raise RuntimeError(
        f"No Java process found matching '{process_name}'. "
        f"Running processes: {result.stdout.strip()}"
    )


async def _collect_thread_dumps(pid: str, output_path: str, count: int, interval: int):
    try:
        with open(output_path, "w") as f:
            for i in range(count):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'=' * 80}\n")
                f.write(f"Thread Dump {i + 1}/{count} at {timestamp} (PID: {pid})\n")
                f.write(f"{'=' * 80}\n\n")
                result = subprocess.run(
                    ["jstack", "-l", pid],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write(f"ERROR: jstack failed: {result.stderr.strip()}\n")
                f.flush()
                if i < count - 1:
                    await asyncio.sleep(interval)
        logger.info("Thread dump collection complete: %s", output_path)
    except Exception as e:
        logger.error("Thread dump collection failed: %s", e)
        with open(output_path, "a") as f:
            f.write(f"\nCOLLECTION ABORTED: {e}\n")


@mcp.tool()
async def capture_thread_dumps(
    process_name: str,
    count: int = 6,
    interval_seconds: int = 5,
) -> dict:
    """
    Find a Java process by name and capture a series of thread dumps using jstack.
    Returns the output file path immediately while dumps are collected in the background.

    Args:
        process_name: Java process name or main class to match (looked up via jps -l)
        count: Number of thread dumps to capture (default: 6)
        interval_seconds: Seconds between each dump (default: 5)

    Returns:
        The absolute path to the file where thread dumps are being written,
        the matched PID, and the estimated completion time in seconds.
    """
    try:
        pid = _find_pid_by_name(process_name)
    except RuntimeError as e:
        return {"error": str(e)}

    output_dir = tempfile.mkdtemp(prefix="threaddumps_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"threaddump_{process_name}_{timestamp}.txt")

    asyncio.create_task(_collect_thread_dumps(pid, output_path, count, interval_seconds))

    return {
        "status": "STARTED",
        "pid": pid,
        "process_name": process_name,
        "file_path": output_path,
        "dump_count": count,
        "interval_seconds": interval_seconds,
        "estimated_completion_seconds": (count - 1) * interval_seconds,
        "message": f"Capturing {count} thread dumps every {interval_seconds}s. "
                   f"File is being written to: {output_path}",
    }


@mcp.tool()
async def http_request(
    url: str,
    method: str = "GET",
    headers: str = "",
    query_params: str = "",
    json_body: str = "",
    form_data: str = "",
    raw_body: str = "",
    content_type: str = "",
    auth_token: str = "",
    timeout: float = 30.0,
    follow_redirects: bool = True,
) -> dict:
    """
    Make an arbitrary HTTP request. Use this for endpoints not covered by other tools.

    Args:
        url: The HTTP/HTTPS URL to call
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
        headers: Optional HTTP headers as a JSON object string, e.g. '{"Accept": "application/json"}'
        query_params: Optional URL query parameters as a JSON object string, e.g. '{"page": "1"}'
        json_body: Request body as a JSON object string, e.g. '{"name": "test"}'
        form_data: Form-encoded body as a JSON object string, e.g. '{"field": "value"}'
        raw_body: Raw string body (set content_type to control Content-Type)
        content_type: Content-Type for raw_body (e.g. "text/xml", "text/plain")
        auth_token: Bearer token for Authorization header
        timeout: Request timeout in seconds (default 30)
        follow_redirects: Whether to follow HTTP redirects (default true)

    Returns:
        Dict with status_code, headers, body (text), and json (parsed if applicable)
    """
    req_headers = json.loads(headers) if headers else {}
    params = json.loads(query_params) if query_params else None
    if auth_token:
        req_headers["Authorization"] = f"Bearer {auth_token}"
    if content_type and raw_body:
        req_headers["Content-Type"] = content_type

    body_kwargs = {}
    if json_body:
        body_kwargs["json"] = json.loads(json_body)
    elif form_data:
        body_kwargs["data"] = json.loads(form_data)
    elif raw_body:
        body_kwargs["content"] = raw_body

    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=follow_redirects
    ) as client:
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=req_headers,
                params=params,
                **body_kwargs,
            )
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            }
            try:
                result["json"] = response.json()
            except (ValueError, TypeError):
                pass
            return result
        except httpx.RequestError as e:
            return {
                "status_code": None,
                "error": type(e).__name__,
                "detail": str(e),
            }


app = mcp.sse_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting MCP Server on http://0.0.0.0:8000")
    logger.info("SSE endpoint available at: http://0.0.0.0:8000/sse")
    uvicorn.run(app, host="0.0.0.0", port=8000)
