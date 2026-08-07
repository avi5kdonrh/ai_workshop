package com.rh;

import io.smallrye.common.annotation.Blocking;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.microprofile.reactive.messaging.Incoming;
import org.eclipse.microprofile.reactive.messaging.Outgoing;

import java.util.UUID;

@Slf4j
@ApplicationScoped
@RequiredArgsConstructor
public class MessageConsumer {

    @Inject
    RepoService repoService;

    @Blocking
    @Incoming("consumer")
    @Transactional
    public void consume(String name) {
        log.info("storing {}",name);
        Person person = Person.builder().name(UUID.randomUUID().toString()).build();
        repoService.persist(person);
        System.out.println(">> Processing Finished "+person.id);
    }


}
