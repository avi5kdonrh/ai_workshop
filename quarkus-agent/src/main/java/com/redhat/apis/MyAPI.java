package com.redhat.apis;

import com.redhat.agents.TraceAgent;
import io.quarkus.mailer.Mailer;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@Path("/analyze")
public class MyAPI  {

    @Inject
    TraceAgent traceAgent;

    /**
     * This mailer is simply configured with a
     * local postfix server that sends an email
     * to /var/spool/mail/user
     */
    @Inject
    Mailer mailer;

    /* *
     * This method is triggerred by the http://localhost:8080/analyze GET call
     * It calls the shortSummary method which gathers a very brief
     * health analysis of the application.
     * This behavior can be modified by changing the system prompt
    * */
    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String chat( String data) {
       return traceAgent.shortSummary();

    }

    /* *
     * This method is triggerred by the http://localhost:8080/analyze/details GET call
     * It calls the detailedAnalysis method which collects a
     * comprehensive analysis on the application's health from the LLM
     * The system prompt instructs the LLM to analyze the tool results and share the conclusion.
     * If the LLM detects a slow component, it can also call the MCP server to collect thread dumps.
     * */
    @Path("/details")
    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String details() {
        String invite = traceAgent.detailedAnalysis();
        // TODO, you can send the email notification optionally
       // mailer.send(Mail.withText("username@localhost", "application performance analysis", invite).setFrom("username@localhost"));
        return invite;

    }
}
