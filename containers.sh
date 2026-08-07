podman run -d --rm --name jaeger -p 16686:16686 -p 4317:4317 -p 4318:4318 jaegertracing/jaeger:latest
podman run -d --rm --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres docker.io/library/postgres:18
podman run -d --rm --name kafka  -p 9092:9092 docker.io/apache/kafka-native:4.2.0
