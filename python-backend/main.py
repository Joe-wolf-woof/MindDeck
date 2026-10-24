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

class AiFieldsRequest(BaseModel):
    term: str

class AiGenRequest(BaseModel):
    term: str
    field: str | None = None

def search_related_terms_from_wikipedia(keyword: str) -> list[str]:
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": keyword, "format": "json", "srlimit": 5}
        headers = {"User-Agent": "MindDeckQuizApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            return [item.get("title") for item in res.json().get("query", {}).get("search", [])]
    except Exception as e:
        print("Wikipedia search error:", e)
    return []

# ① 用語に関連した分野の候補を返すエンドポイント
@app.post("/api/ai-get-fields")
def ai_get_fields(data: AiFieldsRequest):
    term = data.term.strip()
    fields = [f"{term}（専門・学術）", f"{term}（一般・基礎）", f"{term}（IT・テクノロジー）"]
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": term, "format": "json", "srlimit": 3}
        headers = {"User-Agent": "MindDeckApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            snippets = [item.get("title") for item in res.json().get("query", {}).get("search", [])]
            if snippets:
                fields = [f"{s}（関連分野）" for s in snippets[:3]]
    except Exception as e:
        print("Fields error:", e)
    return {"fields": fields}

# ① 選択された分野での解説文＆タグ候補を生成するエンドポイント
@app.post("/api/ai-generate-explanation")
def ai_generate_explanation(data: AiGenRequest):
    term = data.term.strip()
    field = data.field or "一般"
    if not term:
        return {"explanation": "用語が入力されていません。", "tag_candidate": ""}
    
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        params = {"action": "query", "prop": "extracts", "exintro": True, "explaintext": True, "titles": term, "format": "json"}
        headers = {"User-Agent": "MindDeckApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        extract = ""
        if res.status_code == 200:
            pages = res.json().get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1" and "extract" in page_info:
                    extract = page_info["extract"]
        
        if not extract:
            search_params = {"action": "query", "list": "search", "srsearch": f"{term} {field}", "format": "json", "srlimit": 1}
            s_res = requests.get(url, params=search_params, headers=headers, timeout=3)
            if s_res.status_code == 200:
                s_data = s_res.json().get("query", {}).get("search", [])
                if s_data:
                    extract = re.sub(r'<.*?>', '', s_data[0].get("snippet", ""))

        if extract:
            explanation = f"【分野: {field}】\n{extract[:250]}..."
        else:
            explanation = f"「{term}」（分野: {field}）に関する解説文が見つかりませんでした。"
            
        # タグの候補名を作成（例: #専門学術 や #ITテクノロジー などから記号を除外）
        clean_tag = re.sub(r'[（）\s・]', '', field)
        tag_candidate = f"#{clean_tag}"

        return {"explanation": explanation, "tag_candidate": tag_candidate}
    except Exception as e:
        print("AI generation error:", e)

    return {"explanation": "エラーが発生しました。", "tag_candidate": f"#{term}"}

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
    wiki_terms = search_related_terms_from_wikipedia(term)
    for w in wiki_terms:
        if w != term and w not in other_terms and len(w) <= 15:
            other_terms.append(w)
            
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