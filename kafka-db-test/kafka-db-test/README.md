# The Application

## Overview
- This is a typical Quarkus application that exposes a REST API and sends the message to a Kafka topic in the same flow,  
  I have introduced a random delay before the message gets produced to the Kafka topic. This happens in the MyAPI class.
- The MessageConsumer class consumes the message and sends it for processing and persistence. A similar delay is introduced
  before the message is stored in the database to simulate the real time workload.
- The telemetry is sent to an http endpoint exposed by the Jaeger service. Similarly, the application connects to locally available
  Podman containers for Kafka and Postgres.

---

## Server Configuration
*   **Host and Port:** Runs on `0.0.0.0` at port `8082` using vertx.
*   **Transport:** Exposes two REST endpoints at `http://localhost:8082/produce` which produces a random message to a kakfa topic
    with a synthetic delay. The agent should be able to identify this delay in the analysis.
*   **Database Integration:** Uses the Postgres Database running with Podman at localhost:5432
*   **Kafka Integration:** Uses the Kafka broker running with Podman at localhost:9092
*   **Telemetry Export:** Uses the Jaeger service running with Podman to share the generated telemetry at localhost:4317
*   **Full Configuration:** See [application.properties](src/main/resources/application.properties)

---

## Runtime Configuration
- Make sure the jaeger, postgres, and kafka containers are up and running and the corresponding configuration is applied in the application.properties

## Running the Application
```shell script
./run.sh
```
## Testing the Application
- Make a get request at http://localhost:8082/produce to send a random message to topic which generates a few spans and traces that
  are captured by the jaeger telemetry collector. These can be viewed in the jaeger UI at http://localhost:16686/ (select the store-service)
- Additionally, as soon as the application starts, it will send 10 messages to a Kafka topic which should get consumed in the 
  [MessageConsumer](src/main/java/com/rh/MessageConsumer.java), it processes the consumed message through the [RepoService](src/main/java/com/rh/RepoService.java)
  which also has a random delay.

## Dependencies
- JDK 21
- Quarkus 3.37.2
- quarkus-micrometer-opentelemetry 3.37.2
- quarkus-jdbc-postgresql 3.37.2
- quarkus-hibernate-orm 3.37.2
- quarkus-messaging-kafka 3.37.2
- quarkus-rest 3.37.2