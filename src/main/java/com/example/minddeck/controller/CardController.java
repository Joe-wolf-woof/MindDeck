package com.example.minddeck.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.minddeck.model.Card;
import com.example.minddeck.model.Notebook;
import com.example.minddeck.repository.CardRepository;
import com.example.minddeck.repository.NotebookRepository;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class CardController {
    @Autowired private NotebookRepository notebookRepository;
    @Autowired private CardRepository cardRepository;

    @GetMapping("/notebooks")
    public List<Notebook> getAllNotebooks() { return notebookRepository.findAll(); }

    @PostMapping("/notebooks")
    public Notebook createNotebook(@RequestBody Notebook notebook) { return notebookRepository.save(notebook); }

    @GetMapping("/notebooks/{notebookId}/cards")
    public List<Card> getCardsByNotebook(@PathVariable Long notebookId) { return cardRepository.findByNotebookId(notebookId); }

    @PostMapping("/notebooks/{notebookId}/cards")
    public Card createCard(@PathVariable Long notebookId, @RequestBody Card cardRequest) {
        Notebook nb = notebookRepository.findById(notebookId).orElseThrow();
        cardRequest.setNotebook(nb);
        return cardRepository.save(cardRequest);
    }

    @GetMapping("/cards/search")
    public List<Card> searchCards(@RequestParam String keyword) { return cardRepository.searchCards(keyword); }

    @DeleteMapping("/cards/{id}")
    public void deleteCard(@PathVariable Long id) { cardRepository.deleteById(id); }
}