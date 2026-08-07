# Monitoring Agent

## Overview
The Agent application has only two classes, one creates the AI Service (TraceAgent) and another allows the users to
call that service (MyAPI).
The first API (/analyze) calls the LLM API with the system prompt requesting a very brief analysis of the application's health.
The second API (/analyze/details) gets the comprehensive health report and can generate a thread dump if a slow service is detected.

---

## Server Configuration
*   **Host and Port:** Runs on `0.0.0.0` at port `8080` using vertx.
*   **Transport:** Exposes two REST endpoints at `http://localhost:8080/analyze` and `http://localhost:8080/analyze/details`.
*   **MCP Integration:** Uses the locally running MCP server at http://localhost:8000/sse .
*   **LLM Integration:** Uses the custom anthropicp provider that requires the base-url and api-key configuration (see [application.properties](src/main/resources/application.properties).
*   **Mail Integration (Optional):** Uses the local postfix service to share the LLM's analysis.
*   **Full Configuration:** See [application.properties](src/main/resources/application.properties)

---

## Agent's Functions
- The agent exposes two APIs one each for [short analysis](http://localhost:8080/analyze) and [detailed analysis](http://localhost:8080/analyze/details)
- As soon as either of those APIs are called, the Agent shares the system prompt and the available tools and their description with the LLM
- Then the LLM analyzes the system prompt and based on the analysis, triggers a tool call (to the MCP server)
- Now, the result of the last tool call is sent to the LLM (along with the system prompt and the earlier response) and a final analysis
  is fetched which is return to the API's caller.
- The raw interaction with the LLM can be viewed in the quarkus-agent terminal where it is configured to log requests and responses. This can be turned off through application.properties

## Runtime Configuration
```bash
export API_KEY=YOUR_API_KEY
export BASE_URL=VERTEX_API_URL
export FROM="username@localhost"
export MCP_URL="http://localhost:8000/sse"
export LLM_API_HOSTNAME=llmapihost ## replace this with the hostname of your LLM's API this will be used to fetch the ssl certificate.
```

## Running the Agent
```shell script
./run.sh
```
## Dependencies
- JDK 21
- Quarkus 3.37.2
- quarkus-langchain4j 1.12.2
- quarkus-langchain4j-mcp 1.12.2