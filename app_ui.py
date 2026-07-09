import streamlit as st
import requests
import json
 
st.set_page_config(page_title="プロンプト清書アプリ", layout="centered")
 
# セッションメモリ
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "editing_prompt" not in st.session_state:
    st.session_state.editing_prompt = ""
if "first_input" not in st.session_state:
    st.session_state.first_input = ""
 
# サイドバー
with st.sidebar:
    st.image("gyopi.jpg", width=200)
    st.title("ユーザーエリア")
    username = st.text_input("ユーザー名（登録・ログイン）：", value="ナナミ")
    
    if username:
        st.success(f"ログイン中: {username} さん")
        st.write("---")
        st.subheader("過去ログ一覧")
        
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history:
                if chat["role"] == "user":
                    st.caption(f"{chat['message'][:15]}...")
        else:                  
            st.info("ログデータなし")
 
# メイン画面
st.title("目的別プロンプト清書チャット")
st.caption("AI前処理サーバー連携システム")
 
purpose = st.radio(
    "### 利用目的を選んでください：",
    ("🔍 調べもの・技術質問", "💼 就活ES用（自己PR・ガクチカ・志望動機）", "📝 課題・問題の解説", "✂ 長文の要約・抽出")
)
 
st.write("---")
uploaded_file = st.file_uploader("資料・写真・ソースコードなど、任意のファイルを添付してください")
input_url = st.text_input("参考にしてほしいサイトのURLがあれば貼り付けてください：", placeholder="https://example.com/sample-page")
st.write("---")
 
# 過去ログ表示
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"], avatar="👤" if chat["role"] == "user" else "gyopi.jpg"):
        st.write(chat["message"])
 
# チャット入力
user_input = st.chat_input("簡単に指示や内容を入力してください：")
 
# 🎯 【ステップ1】チャット送信で果歩ちゃんのFastAPI（部屋1）を呼び出し、プロンプトを生成
if user_input:
    st.session_state.first_input = user_input
    
    combined_text = user_input
    if uploaded_file is not None:
        combined_text += f"\n(添付ファイル名: {uploaded_file.name})"
    if input_url:
        combined_text += f"\n(参考URL: {input_url})"
 
    # 修正ポイント：FastAPI（ポート8000）の受付窓口を指定
    SERVER_GENERATOR_URL = "http://localhost:8000/api/generate"
    
    # 修正ポイント：FastAPI側の PromptRequest の構造に完全一致させる
    payload = {
        "username": username,
        "purpose": purpose,
        "final_prompt": combined_text
    }
    
    with st.spinner("🤖 第1段階：バックエンドサーバー経由でOllamaが最強プロンプトを構築中..."):
        try:
            response = requests.post(SERVER_GENERATOR_URL, json=payload, timeout=180)
            if response.status_code == 200:
                # 修正ポイント：FastAPIが返す "result" から生成されたプロンプトを抽出
                res_data = response.json()
                if res_data.get("status") == "success":
                    st.session_state.editing_prompt = res_data.get("result", "プロンプト生成失敗")
                else:
                    st.error(f"❌ サーバー内部エラー: {res_data.get('message')}")
            else:
                st.error(f"❌ バックエンドサーバーからエラーが返りました (Status: {response.status_code})")
        except Exception as e:
            st.error(f"❌ FastAPIサーバー（ポート8000）に接続できません。Dockerが起動しているか確認してください: {e}")
            
    st.rerun()
 
# 🎯 【ステップ2】Ollamaが作ったプロンプトを編集して、最終決定ボタンでGeminiへ送信する
if st.session_state.editing_prompt:
    st.write("---")
    with st.chat_message("assistant", avatar="gyopi.jpg"):
        st.write("📝 **Ollamaが構築したプロンプトです。内容を確認・修正してGeminiへ送信してください。**")
        
        final_prompt_input = st.text_area(
            "現在のプロンプト（自由に変更・修正できます）：",
            value=st.session_state.editing_prompt,
            height=300
        )
        
        if st.button("🚀 このプロンプトで最終決定・Geminiへ送信する"):
            st.session_state.chat_history.append({"role": "user", "message": st.session_state.first_input})
 
            # FastAPIのGemini送信エンドポイント（部屋2）を呼び出す
            SERVER_GEMINI_URL = "http://localhost:8000/api/execute-gemini"
            gemini_payload = {
                "final_prompt": final_prompt_input
            }
            
            with st.spinner("✨ 第2段階：Gemini APIが最終的な日本語リライト文章を生成中..."):
                try:
                    response = requests.post(SERVER_GEMINI_URL, json=gemini_payload, timeout=180)
                    if response.status_code == 200:
                        final_answer = response.json().get("result", "回答の取得に失敗しました")
                    else:
                        final_answer = f"❌ サーバーエラー (Status Code: {response.status_code})"
                except Exception as e:
                    final_answer = f"❌ バックエンドサーバーとの通信エラー: {e}"
            
            st.session_state.chat_history.append({"role": "assistant", "message": final_answer})
            
            # メモリ消去してリフレッシュ
            st.session_state.editing_prompt = ""
            st.session_state.first_input = ""
            st.rerun()