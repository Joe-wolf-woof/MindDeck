from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import re
import requests

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

# Wikipedia APIから正解の用語に関連するキーワードを検索して取得する関数
def search_related_terms_from_wikipedia(keyword: str) -> list[str]:
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "format": "json",
            "srlimit": 5
        }
        headers = {"User-Agent": "MindDeckQuizApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            search_results = data.get("query", {}).get("search", [])
            # 検索結果のタイトルを関連用語の候補として抽出
            titles = [item.get("title") for item in search_results]
            return titles
    except Exception as e:
        print("Wikipedia search error:", e)
    return []

@app.post("/api/generate-quiz")
def generate_quiz(data: QuizRequest):
    target = data.target
    all_cards = data.all_cards
    
    term = target.term
    explanation = target.explanation
    
    # 穴埋めまたは解説文の作成
    pattern = re.escape(term)
    if re.search(pattern, explanation, re.IGNORECASE):
        masked_explanation = re.sub(pattern, "[ ＿＿＿＿ ]", explanation, flags=re.IGNORECASE)
    else:
        masked_explanation = f"【解説】\n{explanation}\n\nこの解説が示す用語は何でしょう？"
    
    # 1. 登録されている既存カードから候補を集める
    other_terms = [c.term for c in all_cards if c.term != term]
    
    # 2. ★用語数が少ない場合やバリエーションを増やすため、Wikipediaで関連用語を自動検索
    wiki_terms = search_related_terms_from_wikipedia(term)
    for w in wiki_terms:
        if w != term and w not in other_terms and len(w) <= 15: # 長すぎるタイトルを除外
            other_terms.append(w)
            
    # 3. それでも足りない場合のバックアップ用プール（心理学・IT用語など）
    fallback_pool = [
        "アフォーダンス", "認知バイアス", "スキーマ", "WebXR", 
        "シャドーイング", "メタ認知", "エピソード記憶", "シナプス",
        "ヒューリスティクス", "ワーキングメモリ", "認知負荷", "メンタルモデル"
    ]
    for d in fallback_pool:
        if d not in other_terms and d != term:
            other_terms.append(d)
            
    # 4. 候補の中からランダムに3つ選んでダミー選択肢とする
    selected_dummies = random.sample(other_terms, min(3, len(other_terms)))
    choices = selected_dummies + [term]
    random.shuffle(choices)
    
    return {
        "question": masked_explanation,
        "correct_answer": term,
        "choices": choices
    }