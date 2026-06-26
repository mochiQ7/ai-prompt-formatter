import streamlit as st

st.set_page_config(page_title="プロンプト清書アプリ", layout="centered")

with st.sidebar:
    st.title("👤 ユーザーエリア")
    # 1. ユーザー名入力欄
    username = st.text_input("ユーザー名（登録・ログイン）：", value="ナナミ")
    
    if username:
        st.success(f"ログイン中: {username} さん")
        st.write("---")
        st.subheader("📜 あなたの過去ログ一覧")
        
        # (仮説：橋本くんのDBと繋がったら、ここに本物の過去履歴がズラッと並ぶよ！)
        st.info("⏰ 2026/06/26 10:00\n💼 就活ES用\n「ホテルの宴会サービス...」")
        st.info("⏰ 2026/06/26 09:30\n🔍 調べもの\n「OSI参照モデルについて...」")
    else:
        st.warning("ユーザー名を入力してください")

st.title("🤖 目的別プロンプト清書チャット")
st.caption("AI前処理サーバー連携システム")

# 1.利用目的の選択
purpose = st.radio(
    "【ステップ1】利用目的を選んでください：", 
    ("🔍 調べもの・技術質問", "💼 就活ES用（自己PR）", "📝 課題・問題の解説", "✂ 長文の要約・抽出")
)

st.write("---")
st.subheader("🛠️ ファイルを添付する")

# 2-1.ファイルアップロード欄
uploaded_file = st.file_uploader(
    "資料・写真・ソースコードなど、任意のファイルを添付してください"
)

# 2-2.URL入力欄
input_url = st.text_input(
    "参考にしてほしいサイトのURLがあれば貼り付けてください：",
    placeholder="https://example.com/sample-page"
)

st.write("---")

# 3.テキスト入力
user_input = st.text_area(
    "簡単に内容を入力してください：", 
    placeholder="ここに入力",
    height=150
)

# 4.変換
if st.button("プロンプトを清書する"):
    if user_input or uploaded_file or input_url:
        st.write("---")
        st.subheader("📝 ローカルAIに送信する「清書されたプロンプト」:")
        
        combined_text = ""
        
        # ファイルが添付されている場合の全自動仕分け・読み込み
        if uploaded_file is not None:
            file_name = uploaded_file.name
            combined_text += f"【添付ファイル名】: {file_name}\n"
            
            # 画像形式の場合
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                combined_text += "(※画像データ：Geminiのマルチモーダル機能で直接解析します)\n\n"
            # Office/PDF形式の場合
            elif file_name.lower().endswith('.pdf'):
                combined_text += "(※PDFデータ：バックエンドでテキストを抽出して埋め込みます)\n\n"
            elif file_name.lower().endswith('.docx'):
                combined_text += "(※Wordデータ：バックエンドでテキストを抽出して埋め込みます)\n\n"
            elif file_name.lower().endswith(('.xlsx', '.xls', '.csv')):
                combined_text += "(※データシート：バックエンドでデータ表をテキスト化して埋め込みます)\n\n"
            # それ以外のすべてのファイル（txt, py, md, json, その他すべてのテキスト系）
            else:
                try:
                    # テキストファイルとして読み込む
                    file_contents = uploaded_file.read().decode("utf-8")
                    combined_text += f"--- ファイル中身 ---\n{file_contents}\n-------------------\n\n"
                except Exception:
                    # バイナリファイル（zipなど）で文字として読めなかった場合
                    combined_text += "(※注意：このファイルはテキストとして読み込めない形式、またはバイナリデータです。バックエンド側で特殊解析を行うか、画像/テキスト形式に変換して再試行してください)\n\n"
        
        # URL
        if input_url:
            combined_text += f"【対象の参考URL】: {input_url}\n(※バックエンドでスクレイピングします)\n\n"
            
        # ユーザー指示がある場合
        if user_input:
            combined_text += f"【ユーザーからの指示】: {user_input}\n"
            
        # 最終プロンプトの組み立て
        final_prompt = f"【利用目的】: {purpose}\n\n上記の目的を達成するために、以下の提出された資料や指示をすべて解析し、最高のプロンプトに清書してください。\n\n{combined_text}"
        
        st.text_area("裏側で自動生成されたプロンプト案：", value=final_prompt, height=300)
        # st.success("✨ どんなファイルが来てもクラッシュしない、最強の全方位ファイル受け入れ体制が完成したよ！")
    else:
        st.warning("文章を入力するか、ファイル添付・URL入力をしてください。")