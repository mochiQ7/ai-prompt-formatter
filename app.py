from flask import Flask, render_template

app = Flask(__name__)

# 最初のアドレスにアクセスしたときの処理
@app.route('/')
def home():
    # templatesフォルダの中のindex.htmlを表示する
    return render_template('index.html')

if __name__ == '__main__':
    # デバッグモードをONにしてアプリを起動
    app.run(debug=True)