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

    // 特定ノートブックの単語・カード一覧取得
    @GetMapping("/notebooks/{notebookId}/cards")
    public List<Card> getCardsByNotebookId(@PathVariable Long notebookId) {
        return cardRepository.findByNotebookId(notebookId);
    }

    // 特定ノートブックの単語カード登録
    @PostMapping("/notebooks/{notebookId}/cards")
    public Card createCard(@PathVariable Long notebookId, @RequestBody CardRequest cardRequest) {
        Notebook notebook = notebookRepository.findById(notebookId)
                .orElseThrow(() -> new RuntimeException("Notebook not found"));
        
        Card card = new Card();
        card.setTerm(cardRequest.getTerm());
        card.setExplanation(cardRequest.getExplanation());
        card.setNotebook(notebook);
        
        return cardRepository.save(card);
    }

    // 逆引き全体検索
    @GetMapping("/cards/search")
    public List<Card> searchCards(@RequestParam("keyword") String keyword) {
        return cardRepository.searchCards(keyword);
    }

    // カード削除
    @DeleteMapping("/cards/{id}")
    public void deleteCard(@PathVariable Long id) {
        cardRepository.deleteById(id);
    }

    // リクエスト受信用クラス
    public static class CardRequest {
        private String term;
        private String explanation;

        public String getTerm() { return term; }
        public void setTerm(String term) { this.term = term; }
        public String getExplanation() { return explanation; }
        public void setExplanation(String explanation) { this.explanation = explanation; }
    }
}