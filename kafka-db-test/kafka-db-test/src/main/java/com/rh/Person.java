package com.rh;

import io.quarkus.hibernate.orm.panache.PanacheEntity;
import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Generated;


@Entity
@Table(name = "PERSON")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Person extends PanacheEntityBase {
    @Id
   /* @SequenceGenerator(
            name = "personSequence",
            sequenceName = "person_id_seq",
            allocationSize = 1,
            initialValue = 4)
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "personSequence")*/
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Integer id;

    @Column(name = "NAME")
    private String name;
}
