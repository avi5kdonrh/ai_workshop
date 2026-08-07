export API_KEY=
export BASE_URL=
export FROM="hostname@localhost"
export MCP_URL="http://localhost:8000/sse"
export LLM_API_HOSTNAME=llm_hostname ## Only add the hostname of your llm API (no https, no port), this will be used to extract the certificate.
openssl s_client -connect ${LLM_API_HOSTNAME}:443 </dev/null | openssl x509 -outform PEM > ssl.crt && keytool -import -file ssl.crt -keystore truststore.jks -storepass password -noprompt
mvn clean package && java -jar -Djavax.net.ssl.trustStore=truststore.jks -Djavax.net.ssl.trustStorePassword=password target/quarkus-app/quarkus-run.jar
