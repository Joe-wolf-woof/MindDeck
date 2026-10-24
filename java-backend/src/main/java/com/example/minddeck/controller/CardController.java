package com.example.minddeck.controller;

import com.example.minddeck.model.Card;
import com.example.minddeck.model.Notebook;
import com.example.minddeck.repository.CardRepository;
import com.example.minddeck.repository.NotebookRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class CardController {

    @Autowired
    private CardRepository cardRepository;

    @Autowired
    private NotebookRepository notebookRepository;

    @GetMapping("/notebooks")
    public List<Notebook> getAllNotebooks() {
        return notebookRepository.findAll();
    }

    @PostMapping("/notebooks")
    public Notebook createNotebook(@RequestBody Notebook notebook) {
        return notebookRepository.save(notebook);
    }

    @PutMapping("/notebooks/{id}")
    public Notebook updateNotebook(@PathVariable Long id, @RequestBody Notebook notebookDetails) {
        Notebook notebook = notebookRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Notebook not found"));
        notebook.setTitle(notebookDetails.getTitle());
        return notebookRepository.save(notebook);
    }

    @DeleteMapping("/notebooks/{id}")
    public void deleteNotebook(@PathVariable Long id) {
        notebookRepository.deleteById(id);
    }

    @GetMapping("/notebooks/{notebookId}/cards")
    public List<Card> getCardsByNotebookId(@PathVariable Long notebookId) {
        return cardRepository.findByNotebookId(notebookId);
    }

    @PostMapping("/notebooks/{notebookId}/cards")
    public Card createCard(@PathVariable Long notebookId, @RequestBody CardRequest cardRequest) {
        Notebook notebook = notebookRepository.findById(notebookId)
                .orElseThrow(() -> new RuntimeException("Notebook not found"));
        
        Card card = new Card();
        card.setTerm(cardRequest.getTerm());
        card.setExplanation(cardRequest.getExplanation());
        card.setTags(cardRequest.getTags());
        card.setNotebook(notebook);
        
        return cardRepository.save(card);
    }

    @GetMapping("/cards/search")
    public List<Card> searchCards(@RequestParam(value = "keyword", required = false) String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return cardRepository.findAll();
        }
        return cardRepository.searchCards(keyword);
    }

    @DeleteMapping("/cards/{id}")
    public void deleteCard(@PathVariable Long id) {
        cardRepository.deleteById(id);
    }
    
    // ③ カード更新（ノートブック変更・タグ対応）
    @PutMapping("/cards/{id}")
    public Card updateCard(@PathVariable Long id, @RequestBody CardRequest cardRequest) {
        Card card = cardRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Card not found"));
        
        card.setTerm(cardRequest.getTerm());
        card.setExplanation(cardRequest.getExplanation());
        card.setTags(cardRequest.getTags());
        
        // 別のノートブックへ移動する場合
        if (cardRequest.getNotebookId() != null) {
            Notebook notebook = notebookRepository.findById(cardRequest.getNotebookId())
                    .orElseThrow(() -> new RuntimeException("Notebook not found"));
            card.setNotebook(notebook);
        }
        
        return cardRepository.save(card);
    }

    public static class CardRequest {
        private String term;
        private String explanation;
        private String tags;
        private Long notebookId; // 追加

        public String getTerm() { return term; }
        public void setTerm(String term) { this.term = term; }
        public String getExplanation() { return explanation; }
        public void setExplanation(String explanation) { this.explanation = explanation; }
        public String getTags() { return tags; }
        public void setTags(String tags) { this.tags = tags; }
        public Long getNotebookId() { return notebookId; }
        public void setNotebookId(Long notebookId) { this.notebookId = notebookId; }
    }
}