package com.rh;

import io.opentelemetry.instrumentation.annotations.WithSpan;
import io.smallrye.common.annotation.Blocking;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.reactive.messaging.Channel;
import org.eclipse.microprofile.reactive.messaging.Emitter;
import org.eclipse.microprofile.reactive.messaging.Outgoing;

import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.locks.LockSupport;

@Path("/produce")
public class MyAPI {

    @Inject
    @Channel("producer")
    Emitter<String> messages;

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    @Blocking
    public String produce() {
       return process();
    }


    @WithSpan("producer-thread")
    public String process() {
        LockSupport.parkNanos(Duration.ofSeconds(ThreadLocalRandom.current().nextInt(1,10)).toNanos());
        String message = UUID.randomUUID().toString();
        messages.send(message);
        return "Sent "+message;
    }
}
