from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import re
from duckduckgo_search import DDGS

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

# 広範囲のWebサイトを横断検索する関数
def search_web_general(query: str, max_results=5) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="jp-jp", max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", "")
                })
    except Exception as e:
        print("Web search error:", e)
    return results

# ① 広範囲のWeb検索から分野候補を自動生成
@app.post("/api/ai-get-fields")
def ai_get_fields(data: AiFieldsRequest):
    term = data.term.strip()
    if not term:
        return {"fields": ["コンピュータサイエンス", "経済・ビジネス", "心理学", "一般"]}
    
    fields = []
    # Web全体から用語に関連する専門分野や文脈を検索
    web_results = search_web_general(f"{term} とは 分野 専門", max_results=5)
    for res in web_results:
        title = res.get("title", "")
        # タイトル内の区切り文字（" | "や" - "）から関連分野やカテゴリを抽出
        if " | " in title:
            parts = title.split(" | ")
            if len(parts) > 1 and len(parts[-1]) < 15:
                fields.append(parts[-1].strip())
        elif " - " in title:
            parts = title.split(" - ")
            if len(parts) > 1 and len(parts[-1]) < 15:
                fields.append(parts[-1].strip())

    # 一般的な主要分野もフォールバックとして追加
    default_fields = ["コンピュータサイエンス", "経済・ビジネス", "心理学", "テクノロジー", "一般・基礎"]
    for f in default_fields:
        if f not in fields:
            fields.append(f)
            
    # 重複を除去して最大4個に絞る
    seen = set()
    unique_fields = []
    for f in fields:
        clean_f = re.sub(r'[^\wぁ-んァ-ンー一-龥]', '', f)
        if clean_f and clean_f not in seen and len(clean_f) <= 12:
            seen.add(clean_f)
            unique_fields.append(f)
            
    return {"fields": unique_fields[:4]}

# ② 広範囲のWeb検索結果をAI的に合成して解説文とタグを自動生成
@app.post("/api/ai-generate-explanation")
def ai_generate_explanation(data: AiGenRequest):
    term = data.term.strip()
    field = data.field or "一般"
    if not term:
        return {"explanation": "用語が入力されていません。", "tag_candidate": ""}
    
    try:
        # 選択された分野を考慮してWeb全体を詳細検索
        query = f"{term} {field} 解説 意味"
        web_results = search_web_general(query, max_results=4)
        
        snippets = []
        for r in web_results:
            if r.get("body"):
                snippets.append(r["body"])
                
        if snippets:
            # 複数サイトから得られた解説テキストを合成して要約風に構築
            combined_text = " ".join(snippets)
            explanation = f"【{field}】\n{combined_text[:300]}..."
        else:
            explanation = f"【{field}】\n「{term}」に関するWeb上の解説データが見つかりませんでした。"
            
        # 分野名からタグの候補を生成（例: #コンピュータサイエンス）
        clean_tag = re.sub(r'[（）\s・/]', '', field)
        tag_candidate = f"#{clean_tag}"

        return {"explanation": explanation, "tag_candidate": tag_candidate}
    except Exception as e:
        print("AI generation error:", e)

    return {"explanation": f"【{field}】\nエラーが発生しました。", "tag_candidate": f"#{term}"}

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
        masked_explanation = f"【解説】\n{explanation}\n\n"
    
    other_terms = [c.term for c in all_cards if c.term != term]
    
    # クイズ用の難易度アップ用関連ワードもWeb検索から補填
    web_terms = search_web_general(term, max_results=3)
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