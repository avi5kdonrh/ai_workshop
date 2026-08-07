# AI Workshop
## Overview
- In this workshop, we are building an AI agent that monitors a Quarkus (Java) application, identifies slow running services and even captures further diagnostic information (such as thread dumps) if required.
- The Agent relies on information from the observability API (Jaeger) to determine application's health.

## Prerequisites
- Access to a large language model's API (we are using anthropic's API for this workshop)
- JDK 21 and above
- Podman or Docker
- Python 3.14 or above
- Maven 3.9 
- (Optional) Have a local email server running (Postfix) if you want to share the agent's analysis.

## Technical Information
We will use four projects for this workshop.
 1. **MCP Server (mcp_server.py):** This is written in python and it primarily calls the metrics specific endpoints from the Jaeger API and exacts relevant information from the available telemetry. It can also run some commands on the OS to collect further information. To read more, go to [mcp.md](mcp.md)
 2. **Custom Quarkus Langchain4j Anthropic Libraries (anthropic):** As I am using a Vertex based LLM which has its own URL and authentication mechanism, the default libraries didn't have this level of customization so I created a cloned the [original](https://github.com/quarkiverse/quarkus-langchain4j/tree/main/model-providers/anthropic) library and made some modifications.
 3. **The sample application (kafka-db-test):** This is the application being monitored. It is a Quarkus application that uses several components that you'll see in a real world application such as Kafka, Postgres Database, Rest API, etc. This application sends telemetry to an OTEL collector provided by Jaeger. After analyzing this telemetry, the agent will tell if a component in the application is slow and the reason behind it. For more information go to [application.md](kafka-db-test/kafka-db-test/README.md)
 4. **The Agent (quarkus-agent):** This is where the magic happens. It is a Quarkus Langchain4j based agent that has access to the telemetry API via the MCP [server](mcp.md) I mentioned earlier. Ideally, this would run in a loop constantly monitoring the service but for the purpose of this exercise I've linked the agents to a couple of REST APIs that can be called when required. For more information on this application, go to [agent.md](quarkus-agent/README.md)

## Prepare the project 

```angular2html
./prepare.sh
```

## Open three terminals

### In terminal 1 run:
```shell
python mcp_server.py
```

### In terminal 2 run:
```shell
cd kafka-db-test/kafka-db-test
./run.sh
```
### In terminal 3:

Edit the run.sh and add the api key and LLM url, and LLM host (wherever required) then run:

```shell
cd quarkus-agent
./run.sh
```

### Testing the Agent
- As soon as the [application](kafka-db-test/kafka-db-test) starts, it pushes 10 messages to a Kafka topic. These messages are consumed and persisted to the database.
  All this telemetry is sent to the jaeger collector. The application also exposes a REST API http://localhost:8082/produce that sends a random message to the same Kafka topic.
  The application also periodically exports the telemetry data to Jaeger (can be accessed at http://localhost:16686/search)
- The MCP server has the capability to call the Jaeger API and fetch the service operations or telemetry metrics so now the Agent can utilize it to determine if
  there is any slowness in the application. The Agent exposes two endpoints http://localhost:8080/analyze and http://localhost:8080/analyze/details which perform short and comprehensive application health analysis 
  respectively. The /analyze/details endpoints can also trigger a thread dump for the monitored application if it detects slowness in any operation.

### Cleanup
```shell
podman kill jaeger kafka postgres
kill $(jcmd | grep "kafka-db-test\|quarkus-run" | awk '{print $1}' | xargs)
kill $(netstat -anp | grep 8000 | grep LISTEN | awk '{print $NF}' | cut -d "/" -f 1)
```
