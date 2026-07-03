import json
import urllib.request
import os  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ななみんの画面と繋ぐための許可証
from pydantic import BaseModel

app = FastAPI()

# ---- CORS設定：ななみんの画面（フロントエンド）からの接続を許可 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発テスト環境のためすべてを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# パソコン本体やDockerからキーを自動で読み込みます
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ななみんのStreamlit（payload）の形に完璧に合わせることでエラーを回避！
class PromptRequest(BaseModel):
    username: str
    purpose: str       # ななみんの選択した目的の文字列がそのまま届く
    final_prompt: str  # ななみんが画面で組み立てた「日本語の最強テンプレート付きプロンプト」


@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理・本処理サーバー起動中！"}


# ななみんの画面が呼び出すURL「/api/generate」に窓口を合わせて完全合体！
@app.post("/api/generate")
def clean_prompt(request: PromptRequest):
    # ==========================================
    # 第1段階：ローカルAI（Ollama / Llama 3）でプロンプトを極限まで洗練
    # ==========================================

    # ななみんの画面の選択肢（purpose）と1文字もズレずに完全に一致させて分岐
    if request.purpose == "💼 就活ES用（自己PR・ガクチカ・志望動機）":
        system_prompt = (
            "You are an elite interviewer and an expert prompt engineer. "
            "The user will provide a structured Japanese job-hunting prompt template. "
            "Optimize and rewrite this into a highly professional, logical English meta-prompt. "
            "Instruct the final LLM to evaluate text based on STAR/PREP frameworks and strict criteria. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "Text to append: '[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    elif request.purpose == "🔍 調べもの・技術質問":
        system_prompt = (
            "You are a world-class IT technical expert and senior software engineer. "
            "Optimize the user's structured query template into a deeply technical, logical English prompt. "
            "Ensure it guides the final LLM to provide architectural insights, comparison tables, and trade-offs. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "Text to append: '[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    elif request.purpose == "📝 課題・問題の解説":
        # ななみんのapp_ui.pyにある「📝 課題・問題の解説」の文字と完全連動
        system_prompt = (
            "You are an eminent professor skilled at deep educational reasoning. "
            "Refine the user's educational prompt template into a highly effective English prompt "
            "that guides the final LLM to explain core principles step-by-step with clear logical background. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "Text to append: '[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    else:
        # 「✂ 長文の要約・抽出」およびその他汎用の部屋
        system_prompt = (
            "You are a top-tier publishing editor and expert prompt engineer. "
            "Refine the user's text summary template into an incredibly clean, optimized English prompt. "
            "Enforce strict constraints such as 3 concise bullet points and plain language clear for beginners. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "Text to append: '[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )

    ollama_url = "http://host.docker.internal:11434/api/generate"
    # ななみんがすでに日本語テンプレートで包んでくれた request.final_prompt をLlama 3に投入！
    prompt_data = (
        f"【Instruction】{system_prompt}\n【Structured Prompt Template】{request.final_prompt}"
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
    # 第2段階：外部AI（Gemini API）に投げて日本語で大成功回答を得る
    # ==========================================

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    # Llama 3が英語で超ロジカルに強化してくれたプロンプトをそのままGeminiへパス！
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

    # ななみんの画面が期待している「"result"」というキー名で、Geminiの本物の回答を返却！
    return {
        "status": "success",
        "result": final_answer
    }