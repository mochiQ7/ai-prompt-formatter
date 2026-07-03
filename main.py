import json
import urllib.request
import os  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ななみんの画面と繋ぐための許可証
from pydantic import BaseModel

app = FastAPI()

# ---- CORS設定：相手の画面（フロントエンド）からの接続を許可 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発テスト環境のためすべてを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# パソコン本体やDockerからキーを自動で読み込みます
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class PromptRequest(BaseModel):
    purpose: str  # 利用目的（相手の画面の選択肢がそのまま届きます）
    user_text: str  # ユーザーが入力した雑な文章


@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理・本処理サーバー起動中！"}


@app.post("/api/clean-prompt")
def clean_prompt(request: PromptRequest):
    # ==========================================
    # 第1段階：ローカルAI（Ollama）に英語で清書させる
    # ==========================================

    # 相手の画面の選択肢（purpose）と完全に一致させて分岐します
    if request.purpose == "🔍 調べもの・技術質問":
        system_prompt = (
            "You are a world-class IT technical expert and a university professor in computer science. "
            "Analyze the user's technical question or error. Construct an optimized English prompt "
            "that guides another AI to generate accurate, concise, and fact-based explanations. "
            "Instruct it to create a Markdown comparison table if concepts are compared, provide pros/cons, "
            "and discuss trade-offs or usage precautions based on official documentation. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "'[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    elif request.purpose == "💼 就活ES用（自己PR・ガクチカ・志望動機）":
        system_prompt = (
            "You are an elite interviewer at the forefront of corporate hiring and a professional career advisor. "
            "Analyze the user's raw job-hunting text (Self-PR, Gakuchika, or Motive). "
            "Construct a high-quality English prompt that instructs another AI to: "
            "1) Automatically identify the category and apply the appropriate framework (PREP for Self-PR, STAR for Gakuchika). "
            "2) Transform active/professional business expressions to show strong initiative. "
            "3) Evaluate information sufficiency. If it's insufficient to build a top-tier ES, provide 3 specific interview questions to dig deeper (Pattern A). "
            "If information is sufficient, provide a dramatic rewrite (400 words) and 3 expected tough questions from interviewers (Pattern B). "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "'[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    elif request.purpose == "📝 課題・問題の解説（全科目対応）":
        system_prompt = (
            "You are an eminent emeritus professor skilled at inspiring students. Analyze the user's assignment, math formula, or error. "
            "Construct an optimized English prompt that guides another AI to lead the student to a fundamental understanding rather than rote memorization. "
            "Instruct it to adapt flexibly to any field, break down the logical background/causes step-by-step, and provide next-step hints. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "'[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    else:
        # 「📖 長文の要約・抽出」およびその他すべてはここ（超一流の編集者）
        system_prompt = (
            "You are a top-tier editor at a major publishing house, expert at summarizing complex academic papers and news. "
            "Analyze the user's long text or data. Construct a beautiful English prompt instructing another AI to extract the absolute essence. "
            "Strictly constrain it to a maximum of 3 bullet points, using plain language clear enough for a beginner or middle school student, while strictly keeping factual numbers accurate. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "'[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )

    ollama_url = "http://host.docker.internal:11434/api/generate"
    prompt_data = (
        f"【Instruction】{system_prompt}\n【User Text】{request.user_text}"
    )
    ollama_payload = {
        "model": "llama3",
        "prompt": prompt_data,
        "stream": False,
    }

    try:
        req_ollama = urllib.request.Request(
            ollama_url,
            data=json.dumps(ollama_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_ollama) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            clean_prompt_result = res_body.get("response", "")
    except Exception as e:
        return {
            "status": "error",
            "message": f"第1段階（Ollama）で通信失敗しました: {str(e)}",
        }

    # ==========================================
    # 第2段階：外部AI（Gemini API）に投げて日本語で回答を得る
    # ==========================================

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    gemini_payload = {"contents": [{"parts": [{"text": clean_prompt_result}]}]}

    try:
        req_gemini = urllib.request.Request(
            gemini_url,
            data=json.dumps(gemini_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_gemini) as response:
            res_gemini = json.loads(response.read().decode("utf-8"))
            final_answer = (
                res_gemini.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "Geminiからの応答を取り出せませんでした。")
            )
    except Exception as e:
        final_answer = f"第2段階（Gemini API）との通信に失敗しました。キーが正しいか確認してください: {str(e)}"

    return {
        "status": "success",
        "received_purpose": request.purpose,
        "received_text": request.user_text,
        "generated_english_prompt": clean_prompt_result,
        "reply_message": final_answer,
    }