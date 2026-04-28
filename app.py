import streamlit as st
import json
import os
import requests
import base64
import pandas as pd

st.set_page_config(page_title="AI株式アシスタント", layout="wide")
st.title("📈 AI株式アシスタント")

# GitHub設定（Secretsから取得）
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]  # "user/repo"

DATA_PATH = "data.json"
GITHUB_API = f"https://api.github.com/repos/{REPO}/contents/{DATA_PATH}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------- GitHubからdata.json取得 ----------
def load_data():
    r = requests.get(GITHUB_API, headers=headers)
    content = r.json()["content"]
    sha = r.json()["sha"]

    data = json.loads(base64.b64decode(content).decode())
    return data, sha

def save_data(data, sha):
    encoded = base64.b64encode(
        json.dumps(data, ensure_ascii=False).encode()
    ).decode()

    payload = {
        "message": "update data.json",
        "content": encoded,
        "sha": sha
    }

    requests.put(GITHUB_API, headers=headers, json=payload)

# ---------- 読み込み ----------
data, sha = load_data()

# ---------- 銘柄追加（変更） ----------
st.header("銘柄追加")
symbol = st.text_input("銘柄コード（例: 7203.T）")

if st.button("追加"):
    if symbol not in data["symbols"]:
        data["symbols"].append(symbol)
        save_data(data, sha)
        st.success(f"{symbol} を追加しました")
    else:
        st.warning("既に登録済みです")

# ---------- ニュース ----------
st.header("ニュース追加")
news = st.text_area("AIに教えたい材料")

if st.button("保存"):
    data["extra_news"].append(news)
    save_data(data, sha)
    st.success("保存しました")

# ---------- 結果表示（変更なし） ----------
st.header("AI分析結果")

if os.path.exists("result.json"):
    results = json.load(open("result.json", "r", encoding="utf-8"))
    for r in results:
        st.subheader(r["symbol"])
        st.write("### 結論")
        st.write(r["decision"])
        st.write("### 理由")
        st.write(r["reason"])
        st.write("### 学習")
        st.info(r["education"])

        df = pd.DataFrame(r["chart"])
        st.line_chart(df.set_index("date")["close"])

# ---------- フィードバック ----------
st.header("フィードバック")
fb = st.text_area("実際どうでしたか？")

if st.button("フィードバック送信"):
    json.dump({"feedback": fb}, open("feedback.json", "w", encoding="utf-8"), ensure_ascii=False)
    st.success("保存")
