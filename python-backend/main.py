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

# ① 用語に関連する分野候補を動的に生成して返す
@app.post("/api/ai-get-fields")
def ai_get_fields(data: AiFieldsRequest):
    term = data.term.strip()
    if not term:
        return {"fields": ["コンピュータサイエンス", "生物学", "言語学", "一般"]}
    
    # 基本の主要分野 ＋ Wikipediaの検索結果から得た文脈を組み合わせる
    fields = ["コンピュータサイエンス", "生物学", "言語学", "一般"]
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": term, "format": "json", "srlimit": 3}
        headers = {"User-Agent": "MindDeckApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=3)
        if res.status_code == 200:
            search_results = res.json().get("query", {}).get("search", [])
            for item in search_results:
                title = item.get("title", "")
                if title and title != term and title not in fields:
                    fields.insert(0, title) # 関連性の高そうなものを上位に挿入
        
        # 重複を除いて最大4個に絞る
        seen = set()
        unique_fields = []
        for f in fields:
            if f not in seen:
                seen.add(f)
                unique_fields.append(f)
        fields = unique_fields[:4]
    except Exception as e:
        print("Fields error:", e)
        
    return {"fields": fields}

# ① 選択された分野（例: "コンピュータサイエンス"）に沿った解説文とタグを生成
@app.post("/api/ai-generate-explanation")
def ai_generate_explanation(data: AiGenRequest):
    term = data.term.strip()
    field = data.field or "一般"
    if not term:
        return {"explanation": "用語が入力されていません。", "tag_candidate": ""}
    
    try:
        url = "https://ja.wikipedia.org/w/api.php"
        # 選択された分野の文脈も踏まえて検索
        query = f"{term} {field}" if field != "一般" else term
        
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
            search_params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1}
            s_res = requests.get(url, params=search_params, headers=headers, timeout=3)
            if s_res.status_code == 200:
                s_data = s_res.json().get("query", {}).get("search", [])
                if s_data:
                    extract = re.sub(r'<.*?>', '', s_data[0].get("snippet", ""))

        if extract:
            explanation = f"【{field}】\n{extract[:300]}..."
        else:
            explanation = f"【{field}】\n「{term}」についての解説文が見つかりませんでした。"
            
        # 選択された分野の名前からタグ候補を生成（例: #コンピュータサイエンス）
        clean_tag = re.sub(r'[（）\s・/]', '', field)
        tag_candidate = f"#{clean_tag}"

        return {"explanation": explanation, "tag_candidate": tag_candidate}
    except Exception as e:
        print("AI generation error:", e)

    return {"explanation": f"【{field}分野】\nエラーが発生しました。", "tag_candidate": f"#{term}"}

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