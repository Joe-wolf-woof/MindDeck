from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CardItem(BaseModel):
    term: str
    explanation: str

class QuizRequest(BaseModel):
    target: CardItem
    all_cards: list[CardItem]

@app.post("/api/generate-quiz")
def generate_quiz(data: QuizRequest):
    target = data.target
    all_cards = data.all_cards
    
    term = target.term
    explanation = target.explanation
    
    pattern = re.escape(term)
    if re.search(pattern, explanation, re.IGNORECASE):
        masked_explanation = re.sub(pattern, "[ ＿＿＿＿ ]", explanation, flags=re.IGNORECASE)
    else:
        # ③ 【解説ヒント】を【解説】に統一
        masked_explanation = f"【解説】\n{explanation}\n\nこの解説が示す用語は何でしょう？"
    
    # 選択肢のバリエーション（難易度アップ用プール）
    other_terms = [c.term for c in all_cards if c.term != term]
    fallback_pool = ["アフォーダンス", "認知バイアス", "スキーマ", "WebXR", "シャドーイング", "メタ認知", "エピソード記憶", "シナプス"]
    for d in fallback_pool:
        if d not in other_terms and d != term:
            other_terms.append(d)
            
    selected_dummies = random.sample(other_terms, min(3, len(other_terms)))
    choices = selected_dummies + [term]
    random.shuffle(choices)
    
    return {
        "question": masked_explanation,
        "correct_answer": term,
        "choices": choices
    }