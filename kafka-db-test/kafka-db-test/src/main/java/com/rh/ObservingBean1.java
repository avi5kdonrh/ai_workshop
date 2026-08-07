package com.rh;

import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import org.eclipse.microprofile.reactive.messaging.Channel;
import org.eclipse.microprofile.reactive.messaging.Emitter;

import java.util.UUID;

@ApplicationScoped
class ObservingBean1 {

   @Inject
   @Channel("producer")
   Emitter<String> messages;

   void onShutdown(@Observes ShutdownEvent event) throws InterruptedException {
      System.out.println("Bean1 onShutdown");
      
   }

   void onStart(@Observes StartupEvent event) throws InterruptedException {
      for (int i=0; i<10; i++) {
         System.out.println(">> Sending messages >>");
         messages.send(UUID.randomUUID().toString());
      }
   }
}