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

    // ノートブック一覧取得
    @GetMapping("/notebooks")
    public List<Notebook> getAllNotebooks() {
        return notebookRepository.findAll();
    }

    // ノートブック作成
    @PostMapping("/notebooks")
    public Notebook createNotebook(@RequestBody Notebook notebook) {
        return notebookRepository.save(notebook);
    }

    // ノートブック名変更 (PUT)
    @PutMapping("/notebooks/{id}")
    public Notebook updateNotebook(@PathVariable Long id, @RequestBody Notebook notebookDetails) {
        Notebook notebook = notebookRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Notebook not found"));
        notebook.setTitle(notebookDetails.getTitle());
        return notebookRepository.save(notebook);
    }

    // ノートブック削除 (DELETE)
    @DeleteMapping("/notebooks/{id}")
    public void deleteNotebook(@PathVariable Long id) {
        notebookRepository.deleteById(id);
    }

    // 特定ノートブックの単語・カード一覧取得
    @GetMapping("/notebooks/{notebookId}/cards")
    public List<Card> getCardsByNotebookId(@PathVariable Long notebookId) {
        return cardRepository.findByNotebookId(notebookId);
    }

    // 特定ノートブックの単語カード登録（tags対応）
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

    // 逆引き全体検索
    @GetMapping("/cards/search")
    public List<Card> searchCards(@RequestParam(value = "keyword", required = false) String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return cardRepository.findAll();
        }
        return cardRepository.searchCards(keyword);
    }

    // カード削除
    @DeleteMapping("/cards/{id}")
    public void deleteCard(@PathVariable Long id) {
        cardRepository.deleteById(id);
    }
    
    // カード更新（編集）（tags対応）
    @PutMapping("/cards/{id}")
    public Card updateCard(@PathVariable Long id, @RequestBody CardRequest cardRequest) {
        Card card = cardRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Card not found"));
        
        card.setTerm(cardRequest.getTerm());
        card.setExplanation(cardRequest.getExplanation());
        card.setTags(cardRequest.getTags());
        
        return cardRepository.save(card);
    }

    // リクエスト受信用クラス（tagsフィールドを含む）
    public static class CardRequest {
        private String term;
        private String explanation;
        private String tags;

        public String getTerm() { return term; }
        public void setTerm(String term) { this.term = term; }
        
        public String getExplanation() { return explanation; }
        public void setExplanation(String explanation) { this.explanation = explanation; }
        
        public String getTags() { return tags; }
        public void setTags(String tags) { this.tags = tags; }
    }
}