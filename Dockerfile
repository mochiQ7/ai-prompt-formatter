# Pythonの公式イメージをベースにする
FROM python:3.10-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリのリストをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プログラム全体をコピー
COPY . .

# FastAPIを起動（ポート8000で待ち受け）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]