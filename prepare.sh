./containers.sh
pip-3 install -r requirements.txt
mvn clean install -f anthropic/ -T 8C
mvn clean install -f kafka-db-test/kafka-db-test/ -T 8C
mvn clean install -f quarkus-agent/ -T 8C