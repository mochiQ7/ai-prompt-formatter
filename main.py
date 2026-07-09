import json
import urllib.request
import os  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel                  
 
app = FastAPI()
 
# ---- CORS設定：フロントエンド（Streamlit）からの接続を許可 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境のためすべてを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# 環境変数からGeminiのAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
 
# フロントエンドから送信されるリクエストのデータ構造を定義
class PromptRequest(BaseModel):
    purpose: str       # 利用目的
    final_prompt: str  # 生のエピソード（カフェバイト…）
 
 
@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理・本処理サーバー起動中！"}
 
 
# ==========================================
# 🚪 部屋1：Ollamaでプロンプトを「動的生成」する受付窓口
# ==========================================
@app.post("/api/generate")
def clean_prompt(request: PromptRequest):
    
    # 目的別のメタ指示（Ollamaへの命令は英語で出しつつ、成果物は100%日本語に固定する）
    if "就活ES" in request.purpose or "自己PR" in request.purpose:
        system_prompt = (
            "You are an elite interviewer and an expert prompt engineer. "
            "Analyze the user's input and generate a highly structured, professional prompt in JAPANESE for Gemini. "
            "The output must be a well-crafted Japanese instruction that sets a persona of a professional career advisor, "
            "includes the user's experience, and enforces strict output formats (PREP/STAR methods). "
            "⚠️Strict Rule: Output ONLY the final Japanese prompt. No English, no explanations, no greetings."
        )
    elif "調べもの" in request.purpose or "技術質問" in request.purpose:
        system_prompt = (
            "You are a world-class IT technical expert. "
            "Generate a deeply technical, logical prompt in JAPANESE for Gemini based on the user's question. "
            "The output prompt must instruct Gemini to provide clear explanations and comparison tables. "
            "⚠️Strict Rule: Output ONLY the final Japanese prompt. No English, no explanations, no greetings."
        )
    elif "課題" in request.purpose or "問題" in request.purpose:
        system_prompt = (
            "You are an eminent professor. "
            "Generate a highly effective prompt in JAPANESE for Gemini that guides a student step-by-step through core principles. "
            "The output prompt must instruct Gemini to explain causes and logical steps. "
            "⚠️Strict Rule: Output ONLY the final Japanese prompt. No English, no explanations, no greetings."
        )
    else:
        system_prompt = (
            "You are a top-tier publishing editor. "
            "Generate an optimized summary prompt in JAPANESE for Gemini based on the user's text. "
            "The output prompt must instruct Gemini to summarize points into strictly 3 clear bullets. "
            "⚠️Strict Rule: Output ONLY the final Japanese prompt. No English, no explanations, no greetings."
        )
 
    ollama_url = "http://host.docker.internal:11434/api/generate"
   
    # ユーザーのエピソードとシステム命令を結合
    prompt_data = f"【Instruction】{system_prompt}\n【User Input】\"{request.final_prompt}\" (Purpose: {request.purpose})"
    
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
            "message": f"Ollamaとの通信に失敗しました: {str(e)}",
        }
 
    # フロントエンドが待っている "result" というキーで結果を返す
    return {
        "status": "success",
        "result": clean_prompt_result
    }
 
 
# ==========================================
# 🚪 部屋2：修正されたプロンプトを「Gemini」に送信する受付窓口
# ==========================================
class GeminiRequest(BaseModel):
    final_prompt: str
 
@app.post("/api/execute-gemini")
def execute_gemini(request: GeminiRequest):
   
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
   
    gemini_payload = {"contents": [{"parts": [{"text": request.final_prompt}]}]}
 
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
        final_answer = f"Gemini APIとの通信に失敗しました。APIキーまたはネットワークを確認してください: {str(e)}"
 
    return {
        "status": "success",
        "result": final_answer
    }