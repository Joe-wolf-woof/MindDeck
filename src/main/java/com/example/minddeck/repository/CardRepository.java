package com.example.minddeck.repository;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.example.minddeck.model.Card;

public interface CardRepository extends JpaRepository<Card, Long> {
    List<Card> findByNotebookId(Long notebookId);

    @Query("SELECT c FROM Card c WHERE c.term LIKE %:keyword% OR c.explanation LIKE %:keyword%")
    List<Card> searchCards(@Param("keyword") String keyword);
}