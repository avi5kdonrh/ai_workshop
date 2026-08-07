# HTTP Endpoint MCP Server

## Overview
The **HTTP Endpoint MCP Server** is a Model Context Protocol (MCP) server built using the `FastMCP` framework[cite: 1]. It provides a suite of observability and diagnostic tools, primarily integrating with a local Jaeger instance to analyze service traces[cite: 1]. Additionally, it includes system-level debugging utilities, such as automated Java thread dump collection[cite: 1].

---

## Server Configuration
*   **Host and Port:** Runs on `0.0.0.0` at port `8000` using Uvicorn[cite: 1].
*   **Transport:** Exposes a Server-Sent Events (SSE) endpoint at `http://0.0.0.0:8000/sse`[cite: 1].
*   **Jaeger Integration:** Defaults to a local Jaeger instance at `http://localhost:16686`[cite: 1].

---

## Available MCP Tools

### 1. Jaeger Trace Analysis Tools
These tools interact with Jaeger's HTTP API to fetch and analyze traces[cite: 1].

| Tool Name | Description | Key Capabilities |
| :--- | :--- | :--- |
| **`get_service_health`** | Retrieves an aggregated health summary for a service[cite: 1]. | Calculates throughput, error rates, latency percentiles (p50, p95, p99), and provides a breakdown of top operations and errors[cite: 1]. |
| **`get_service_operations`** | Lists all known operations for a specific service[cite: 1]. | Direct fetch from Jaeger's `/api/services/{service}/operations` endpoint[cite: 1]. |
| **`compare_service_health`** | Compares service health across two time windows to detect regressions[cite: 1]. | Highlights regressions if the error rate increases by more than 2% or if the p95 latency jumps by more than 20%[cite: 1]. |

### 2. System & Diagnostic Tools
These tools provide deeper application-level diagnostics and general network utility[cite: 1].

*   **`capture_thread_dumps`**
    *   Locates a running Java process by name using the `jps -l` command[cite: 1].
    *   Captures a configurable series of thread dumps using `jstack`[cite: 1].
    *   > **Note:** Thread dumps are collected asynchronously[cite: 1]. The tool immediately returns the estimated completion time and the absolute path to the output file[cite: 1].
*   **`http_request`**
    *   A versatile HTTP client for making arbitrary requests to external endpoints[cite: 1].
    *   Supports configurable methods, headers, query parameters, JSON/form/raw bodies, and authorization tokens[cite: 1].

---

## Dependencies
This project requires the following primary Python libraries[cite: 1]:
*   **`mcp`**: Provides the `FastMCP` framework used to build the server[cite: 1].
*   **`httpx`**: Powers asynchronous HTTP requests to Jaeger and other external APIs[cite: 1].
*   **`uvicorn`**: Used to serve the ASGI application on port `8000`[cite: 1].
*   **Standard Libraries**: Relies on `subprocess` and `asyncio` for executing underlying shell commands (`jps`, `jstack`) and managing background tasks[cite: 1].