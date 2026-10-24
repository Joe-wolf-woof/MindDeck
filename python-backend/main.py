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
    tags: str | None = None

class QuizRequest(BaseModel):
    target: CardItem
    all_cards: list[CardItem]

class AiGenRequest(BaseModel):
    term: str

# Wikipedia APIから関連用語を検索して取得する関数（クイズ難易度アップ用）
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
            return [item.get("title") for item in search_results]
    except Exception as e:
        print("Wikipedia search error:", e)
    return []

# ③ 用語から解説を自動生成するAIエンドポイント
@app.post("/api/ai-generate-explanation")
def ai_generate_explanation(data: AiGenRequest):
    term = data.term.strip()
    if not term:
        return {"explanation": "用語が入力されていません。"}
    
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        # 1. Wikipediaのイントロ文章を自動取得
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": term,
            "format": "json"
        }
        headers = {"User-Agent": "MindDeckApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            pages = res.json().get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1" and "extract" in page_info:
                    extract = page_info["extract"]
                    if extract:
                        return {"explanation": extract[:250] + ("..." if len(extract) > 250 else "")}
        
        # 2. 見つからない場合は検索スニペットを利用
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": term,
            "format": "json",
            "srlimit": 1
        }
        s_res = requests.get(url, params=search_params, headers=headers, timeout=3)
        if s_res.status_code == 200:
            s_data = s_res.json().get("query", {}).get("search", [])
            if s_data:
                snippet = re.sub(r'<.*?>', '', s_data[0].get("snippet", ""))
                return {"explanation": f"{snippet}..."}
                
    except Exception as e:
        print("AI generation error:", e)

    return {"explanation": f"「{term}」に関する自動解説が見つかりませんでした。手動で入力してください。"}

# クイズ生成エンドポイント
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
        masked_explanation = f"【解説】\n{explanation}\n\nこの解説が示す用語は何でしょう？"
    
    other_terms = [c.term for c in all_cards if c.term != term]
    
    # 関連用語をWikipediaから補填してダミーの難易度を上げる
    wiki_terms = search_related_terms_from_wikipedia(term)
    for w in wiki_terms:
        if w != term and w not in other_terms and len(w) <= 15:
            other_terms.append(w)
            
    fallback_pool = [
        "アフォーダンス", "認知バイアス", "スキーマ", "WebXR", 
        "シャドーイング", "メタ認知", "エピソード記憶", "シナプス",
        "ヒューリスティクス", "ワーキングメモリ", "認知負荷", "メンタルモデル"
    ]
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