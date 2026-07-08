from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 画面から送られてくるデータの形を定義
class PromptPayload(BaseModel):
    username: str
    purpose: str
    final_prompt: str

# 画面からデータが飛んできたときの受け皿（APIエンドポイント）
@app.post("/api/generate")
def generate_response(payload: PromptPayload):
    # ターミナルに、画面からデータが届いたことを表示する（デバッグ用）
    print(f"受信成功　ユーザー: {payload.username} / 目的: {payload.purpose}")
    
    # 画面（Streamlit）に返す返事のデータ
    return {
        "result": f"【擬似サーバーからの応答】\n{payload.username}さん、リクエストを受信。選んだ目的は「{payload.purpose}」。\n画面から送られてきたプロンプトの文字数は {len(payload.final_prompt)} 文字でした。"
    }