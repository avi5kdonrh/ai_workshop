package com.rh;

import io.opentelemetry.instrumentation.annotations.WithSpan;
import jakarta.enterprise.context.ApplicationScoped;

import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.locks.LockSupport;

@ApplicationScoped
public class RepoService {

    @WithSpan("persistence-layer")
    public void persist(Person person) {
        LockSupport.parkNanos(Duration.ofSeconds(ThreadLocalRandom.current().nextInt(1,10)).toNanos());
        person.persist();
    }
}
