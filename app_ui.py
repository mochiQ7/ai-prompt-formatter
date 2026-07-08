import streamlit as st
import requests

st.set_page_config(page_title="プロンプト清書アプリ", layout="centered")

TEMPLATE_SEARCH = """【役割】
あなたは世界最高峰のITテクニカルエキスパートおよび情報工学の大学教授です。

【目的】
ユーザーからの技術的な質問や疑問に対して、正確、簡潔、かつ客観的な事実に基づいた解説プロンプトを生成してください。

【制約条件】
- 概念の比較が生じる場合は、必ずMarkdownの【比較表】を作成して視覚的に分かりやすくすること。
- メリットだけでなく、デメリットやトレードオフ、使用上の注意点も必ず提示すること。
- 出典や公式ドキュメントに基づく正確な情報をベースにすること。

【入力データ（ユーザーの質問）】
{input_text}

【出力フォーマット】
1. 概要（一言で言うと）
2. 詳細解説（比較表や箇条書き）
3. メリット・デメリット
"""

TEMPLATE_ES = """【役割】
あなたは企業の採用最前線で何千人もの学生を面接してきた「超一流の採用面接官」であり、プロのキャリアアドバイザーです。

【目的】
ユーザーが入力した就活の原稿（自己PR、ガクチカ、志望動機、または雑多な箇取りのエピソード）を読み解き、書類選考を圧倒的な高評価で通過し、面接でも無双できるレベルの完成度に引き上げるための指示文を生成してください。

【制約条件】
- 【入力の自動判別】: 入力された内容が「自己PR」「ガクチカ」「志望動機」のどれに該当するかをAIに判断させ、以下の最適なフレームワークを適用して推敲すること。
  - 自己PR ➡ PREP法（結論、理由、具体例、貢献）
  - ガクチカ ➡ STAR法（状況、課題、行動、結果）
  - 志望動機 ➡ 成し遂げたいこと、その原体験（なぜこの会社か）、自分の強みの活かし方
- 【表現のビジネス化】: 学生らしい曖昧な表現や受動的な表現を、当事者意識と行動力が伝わるプロっぽいビジネス用語へ言い換えること。
- 【情報十分性の評価】: ユーザーの入力データを確認し、具体的なエピソード、数値実績、行動の動機、直面した課題などの「深み」が不足しているか評価すること。
- 【対話型インタビューの実行】: もし情報が不足しており、このままではクオリティの高いESが作れないと判断した場合は、無理に完成案を作ろうとせず、不足している要素を埋めるための【具体的な逆質問（インタビュー）】を3点以内で作成すること。
- 【情報の蓄積】: すでにユーザーから引き出せている情報がある場合は、それをベースに構築を進めること。
- 文字数は特に指定がない限り【400文字前後】に美しく収めること。

【入力データ（学生の就活テキスト】
{input_text}

【出力フォーマット】
以下の状況に応じて、どちらか一方のフォーマットのみを選択して出力してください。

■ パターンA：【情報不足のためインタビューを継続する】場合
1. 判断：[情報不足のためインタビューを継続する]
2. 判別されたカテゴリー：（自己PR / ガクチカ / 志望動機）
3. ユーザーへの逆質問（インタビュー）：（不足している要素を埋める質問を3点以内で記載）

■ パターンB：【情報が十分なのでES作成に進む】場合
1. 判断：[情報が十分なのでES作成に進む]
2. 判別されたカテゴリー：（自己PR / ガクチカ / 志望動機）
3. 劇的リライト案（400文字）
4. 【面接対策】このESを見た面接官が確実に突っ込んでくる「想定深掘り質問」3選

"""

TEMPLATE_EXPLAIN = """【役割】
あらゆる学問に精通し、学生のモチベーションを引き出すのが天才的に上手い「大学の優秀な名誉教授」です。

【目的】
ユーザーが提示した課題の疑問、エラー、数式、レポートのテーマ、または理解できない概念について、単に答えを丸暗記させるのではなく、本質的な理解へ導くための解説プロンプトを生成してください。

【制約条件】
- プログラミング、数学、文系レポートなど、あらゆる分野の課題に対して柔軟に適応すること。
- 単に正解や結論を教えるだけでなく、なぜその問題が生じるのか、なぜその考え方をするのかという【論理的な背景・原因】を分かりやすく噛み砕くこと。
- 理解を深めるために、解説は【ステップバイステップ（段階的）】で論理的に展開すること。
- 学生が自力で次のステップ（レポート執筆や類題演習）に進めるよう、具体的な「次へのヒント」を提示すること。

【入力データ（課題・問題・エラー・疑問点）】
{input_text}

【出力フォーマット】
1. 疑問・問題の本質的な原因（なぜ難しいのか、なぜエラーなのか）
2. ステップバイステップの論理的解説
3. 課題を完成させるための「次の一歩（ヒント）」
"""

TEMPLATE_SUMMARY = """【役割】
あなたは大手出版社で数々の難解な論文やニュースを要約してきた「超一流の編集者」です。

【目的】
提示された長文のテキスト、論文、レジュメ、またはWebサイトのスクレイピングデータから、エッセンスだけを極限まで抽出した美しい要約プロンプトを生成してください。

【制約条件】
- 元の文章がどれだけ長くても、重要なポイントを【厳選して箇条書きで3点以内】にまとめること。
- 専門用語や難しい漢字は、IT初心者や中学生でも直感的に理解できる平易な言葉に翻訳（言い換え）すること。
- 事実を歪曲せず、元の文章に含まれる数値やファクトは正確に保持すること。

【入力データ（対象の長文テキスト）】
{input_text}

【出力フォーマット】
■ 3行要約
- 1点目
- 2点目
- 3点目
"""

# セッションメモリ
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # 過去のチャットログ
if "editing_prompt" not in st.session_state:
    st.session_state.editing_prompt = "" # 修正するプロンプト
if "first_input" not in st.session_state:
    st.session_state.first_input = "" # ユーザーが最初に入力した指示

# サイドバー
with st.sidebar:
    st.image("gyopi.jpg", width=200)
    st.title("ユーザーエリア")
    # ユーザー名入力欄
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
            # まだ一度も送信ボタンを押していない時
            st.info("ログデータなし")
    else:
        st.warning("ユーザー名を入力してください")

# メイン画面
st.title("目的別プロンプト清書チャット")
st.caption("AI前処理サーバー連携システム")

# 利用目的の選択
st.markdown("### 利用目的を選んでください：")
purpose = st.radio(
    "",
    ("🔍 調べもの・技術質問", "💼 就活ES用（自己PR・ガクチカ・志望動機）", "📝 課題・問題の解説", "✂ 長文の要約・抽出")
)

st.write("---")
st.subheader("🛠️ ファイルを添付する")

# ファイルアップロード欄
uploaded_file = st.file_uploader(
    "資料・写真・ソースコードなど、任意のファイルを添付してください"
)
# URL入力欄
input_url = st.text_input(
    "参考にしてほしいサイトのURLがあれば貼り付けてください：",
    placeholder="https://example.com/sample-page"
)
st.write("---")


# 過去のチャットタイムライン表示
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"], avatar="👤" if chat["role"] == "user" else "gyopi.jpg"):
        st.write(chat["message"])

# チャット入力欄
user_input = st.chat_input(
    "簡単に指示や内容を入力してください：", 
)

if user_input:
    # 1.すでにプロンプトを作成中で、追加のチャット指示が来た場合
    if st.session_state.editing_prompt:
        st.session_state.editing_prompt += f"\n\n# 追加修正要求:\n- {user_input}\n- 上記の要求を最優先でプロンプトの#制約条件に組み込んで、全体の構成を維持したままアップデートしてください。"
        st.rerun()
        
    # 2.最初の入力の場合
    else:
        st.session_state.first_input = user_input
        combined_text = f"-ユーザーからの指示: {user_input}\n"
        
        if uploaded_file is not None:
            file_name = uploaded_file.name
            combined_text += f"-添付ファイル名: {file_name}\n"
        
        if input_url:
            combined_text += f"-参考URL: {input_url}\n"
    
        if purpose == "🔍 調べもの・技術質問":
            st.session_state.editing_prompt = TEMPLATE_SEARCH.format(input_text=combined_text)
        elif purpose == "💼 就活ES用（自己PR・ガクチカ・志望動機）":
            st.session_state.editing_prompt = TEMPLATE_ES.format(input_text=combined_text)
        elif purpose == "📝 課題・問題の解説（全科目対応）":
            st.session_state.editing_prompt = TEMPLATE_EXPLAIN.format(input_text=combined_text)
        else:
            st.session_state.editing_prompt = TEMPLATE_SUMMARY.format(input_text=combined_text)
            
        st.rerun()

# プロンプト確認・編集・送信
if st.session_state.editing_prompt:
    st.write("---")
    with st.chat_message("assistant", avatar="gyopi.jpg"):
        st.write("このテキストボックス内を直接修正、または下のチャット欄に追加の指示を入力")
        
        # テキストエリア
        final_prompt_input = st.text_area(
            "現在のプロンプト：", 
            value=st.session_state.editing_prompt, 
            height=300
        )
        st.session_state.editing_prompt = final_prompt_input
        
        # 最終送信ボタン
        if st.button("🚀 このプロンプトで最終送信する"):
            st.session_state.chat_history.append({
                "role": "user", 
                "message": st.session_state.first_input
            })

            # API通信処理
            SERVER_URL = "http://localhost:8000/api/generate"
            payload = {
                "username": username, 
                "purpose": purpose, 
                "final_prompt": final_prompt_input
            }
            
            try:
                # 擬似サーバー（または本物）への送信
                response = requests.post(SERVER_URL, json=payload)
                api_result = response.json().get("result")
            
            except Exception as e:
                backticks = "```"
                api_result = f"""### ぎょぴちゃんAIからの回答

**🚀 送信された最終プロンプト:**
{backticks}text
{final_prompt_input}
{backticks}

（※現在はテスト通信モードです。インフラ合体後に本物のGeminiの答えがここに出るよ！）"""    
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "message": api_result
            })
            
            # クリーンアップ
            st.session_state.editing_prompt = ""
            st.session_state.first_input = ""
            st.rerun()