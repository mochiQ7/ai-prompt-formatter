from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "success", "message": "AI前処理サーバー起動中！"}