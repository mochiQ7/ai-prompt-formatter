import json
import urllib.request
import os  
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# (パソコン本体やDockerからキーを自動で読み込みます)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class PromptRequest(BaseModel):
    purpose: str  # 利用目的 (例: "就活ES用")
    user_text: str  # ユーザーが入力した雑な文章


@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理・本処理サーバー起動中！"}


@app.post("/api/clean-prompt")
def clean_prompt(request: PromptRequest):
    # ==========================================
    # 第1段階：ローカルAI（Ollama）に英語で清書させる
    # ==========================================

    # 1. Llama 3が一番実力を発揮できる「英語の命令書き」に変更！
    # ※ 最後にGeminiへ引き渡すための「日本語で回答して」という厳格なルール文を末尾に添えるように指示します。
    if request.purpose == "就活ES用":
        system_prompt = (
            "You are a professional career counselor. Analyze the user's raw experience text "
            "and structuralize it into a high-quality prompt in English based on the STAR framework. "
            "At the very end of your response, you MUST always append this exact rule text verbatim: "
            "'[Strict Rule: Please provide the final output in natural, professional, and polite Japanese.]'"
        )
    else:
        system_prompt = (
            "You are an expert prompt engineer. Refine the user's ambiguous input into a structured, "
            "clear, and optimized prompt in English with roles, constraints, and formatting. "
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

    # 2. Gemini APIの送り先URLを設定（最新の2.5-flashモデルを使用します）
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    # Ollamaが作った英語の最強プロンプトをそのままGeminiのデータにはめ込む
    gemini_payload = {"contents": [{"parts": [{"text": clean_prompt_result}]}]}

    try:
        req_gemini = urllib.request.Request(
            gemini_url,
            data=json.dumps(gemini_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_gemini) as response:
            res_gemini = json.loads(response.read().decode("utf-8"))
            # Geminiから返ってきた最終的な「日本語の回答」を取り出す
            final_answer = (
                res_gemini.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "Geminiからの応答を取り出せませんでした。")
            )
    except Exception as e:
        final_answer = f"第2段階（Gemini API）との通信に失敗しました。キーが正しいか確認してください: {str(e)}"

    # 3. 画面側には、Ollamaが作った「英語のプロンプト」と、Geminiが作った「日本語の最終回答」の両方を送り返す
    return {
        "status": "success",
        "received_purpose": request.purpose,
        "received_text": request.user_text,
        "generated_english_prompt": clean_prompt_result,  # ローカルAIが作った英語プロンプト
        "reply_message": final_answer,  # 【本物】Geminiが日本語で書いてくれた最終成果物！
    }