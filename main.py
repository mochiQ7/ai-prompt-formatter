import json
import urllib.request
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class PromptRequest(BaseModel):
    purpose: str  # 利用目的 (例: "就活ES用")
    user_text: str  # ユーザーが入力した雑な文章


@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理サーバー起動中！"}


# 【合体版】ななみんの画面からデータを受け取り、Ollamaに清書させる窓口
@app.post("/api/clean-prompt")
def clean_prompt(request: PromptRequest):
    # 1. ユーザーが選んだモード（目的）に合わせて、裏で渡すテンプレート（命令書き）を切り替える
    if request.purpose == "就活ES用":
        system_prompt = "あなたは就活支援のプロです。ユーザーの雑なエピソードを、[結論(ガクチカ)][行動][結果]の美しい構成のプロンプトに清書してください。"
    else:
        system_prompt = "あなたは優秀なプロンプトエンジニアです。ユーザーの曖昧な指示文を、役割・制約・出力フォーマットを整えた最高のプロンプトに清書してください。"

    # 2. パソコン本体で動いているOllama(Llama 3)の住所を設定
    # ※ Docker内からホストPCに通信するため「host.docker.internal」を使います
    ollama_url = "http://host.docker.internal:11434/api/generate"

    # AIに渡すデータを組み立てる
    prompt_data = (
        f"【指示】{system_prompt}\n【清書する文章】{request.user_text}"
    )
    payload = {"model": "llama3", "prompt": prompt_data, "stream": False}

    # 3. Ollamaに「これ清書して！」とデータを送信する
    try:
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            # AIが考えてくれた清書結果を取り出す
            ai_response = res_body.get("response", "AIからの応答が空でした。")
    except Exception as e:
        ai_response = f"Ollama(AI)との通信に失敗しました: {str(e)}"

    # 4. 完成した清書プロンプトを画面側に送り返す
    return {
        "status": "success",
        "received_purpose": request.purpose,
        "received_text": request.user_text,
        "reply_message": ai_response,  # ここに本物のローカルAIの回答が入ります！
    }