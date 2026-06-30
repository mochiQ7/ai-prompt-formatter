from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# ななみんの画面から送られてくるデータの形を定義する
class PromptRequest(BaseModel):
    purpose: str     # 利用目的 (例: "就活ES用")
    user_text: str   # ユーザーが入力した雑な文章

@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理サーバー起動中！"}

# ななみんの画面からデータを受け取る窓口
@app.post("/api/clean-prompt")
def clean_prompt(request: PromptRequest):
    # 画面から届いたデータを一旦確認する
    print(f"受け取った目的: {request.purpose}")
    print(f"受け取ったテキスト: {request.user_text}")
    
    return {
        "status": "success",
        "received_purpose": request.purpose,
        "received_text": request.user_text,
        "reply_message": "サーバー側でデータを受け取りました！(ここにAIの回答が入る予定です)"
    }