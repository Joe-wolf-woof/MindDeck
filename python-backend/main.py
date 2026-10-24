import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import re
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各種APIキーの設定（※RenderのEnvironment環境変数から読み込まれます）
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "YOUR_SERPER_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# Gemini APIの初期化（最新の推奨モデルに変更）
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel("gemini-2.0-flash")

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

# Serper.dev（Google検索API）を使ってGoogle検索を行う関数
def search_google_serper(query: str, num_results=4) -> list[dict]:
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "gl": "jp",
        "hl": "ja",
        "num": num_results
    }
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            organic = data.get("organic", [])
            results = []
            for item in organic:
                results.append({
                    "title": item.get("title", ""),
                    "body": item.get("snippet", ""),
                    "href": item.get("link", "")
                })
            return results
    except Exception as e:
        print("Serper API error:", e)
    return []

# ① Serper.devの検索結果から分野候補を自動抽出
@app.post("/api/ai-get-fields")
def ai_get_fields(data: AiFieldsRequest):
    term = data.term.strip()
    if not term:
        return {"fields": ["コンピュータサイエンス", "経済・ビジネス", "心理学", "一般"]}
    
    fields = []
    web_results = search_google_serper(f"{term} とは 分野 専門", num_results=4)
    for res in web_results:
        title = res.get("title", "")
        if " | " in title:
            parts = title.split(" | ")
            if len(parts) > 1 and len(parts[-1]) < 15:
                fields.append(parts[-1].strip())
        elif " - " in title:
            parts = title.split(" - ")
            if len(parts) > 1 and len(parts[-1]) < 15:
                fields.append(parts[-1].strip())

    default_fields = ["コンピュータサイエンス", "経済・ビジネス", "心理学", "テクノロジー", "一般・基礎"]
    for f in default_fields:
        if f not in fields:
            fields.append(f)
            
    seen = set()
    unique_fields = []
    for f in fields:
        clean_f = re.sub(r'[^\wぁ-んァ-ンー一-龥]', '', f)
        if clean_f and clean_f not in seen and len(clean_f) <= 12:
            seen.add(clean_f)
            unique_fields.append(f)
            
    return {"fields": unique_fields[:4]}

# ② 【RAG方式】Serper.dev（Google検索） ＋ Geminiによる要約・解説生成
@app.post("/api/ai-generate-explanation")
def ai_generate_explanation(data: AiGenRequest):
    term = data.term.strip()
    field = data.field or "一般"
    if not term:
        return {"explanation": "用語が入力されていません。", "tag_candidate": ""}
    
    # Step 1: Serper.devでGoogle検索し、関連情報を収集
    query = f"{term} {field} 意味 定義"
    web_results = search_google_serper(query, num_results=4)
    
    snippets = [r["body"] for r in web_results if r.get("body")]
    context = "\n".join(snippets) if snippets else "特に関連する詳細なWeb情報が見つかりませんでした。"

    # Step 2: Gemini API に検索情報を読ませて綺麗な解説文に要約させる（RAG）
    prompt = f"""
    あなたは学習用単語帳のAIアシスタントです。
    以下のGoogle検索から得られた参考情報を基に、「{term}」という用語について、「{field}」の分野における解説文を作成してください。

    【検索された参考情報】
    {context}

    【出力の条件】
    1. 学習用単語帳として分かりやすく、150〜250文字程度の解説文にまとめてください。
    2. 文頭に必ず「【{field}分野の解説】」と記載してください。
    3. 出力は解説文のテキストのみにしてください。
    """

    try:
        response = ai_model.generate_content(prompt)
        explanation = response.text.strip()
    except Exception as e:
        print("Gemini API error:", e)
        explanation = f"【{field}分野】\nAIによる解説の要約生成に失敗しました。"

    # タグ候補の生成（例: #コンピュータサイエンス）
    clean_tag = re.sub(r'[（）\s・/]', '', field)
    tag_candidate = f"#{clean_tag}"

    return {
        "explanation": explanation,
        "tag_candidate": tag_candidate
    }

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
    
    web_terms = search_google_serper(term, num_results=3)
    for wt in web_terms:
        title = wt.get("title", "")
        if title and title != term and len(title) <= 15 and title not in other_terms:
            other_terms.append(title)
            
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