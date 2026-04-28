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

# ---------- 結果表示（analysis_today使用） ----------
st.header("📊 今日のAI分析一覧")

if os.path.exists("analysis_today.json"):
    with open("analysis_today.json", "r", encoding="utf-8") as f:
        analysis = json.load(f)

    st.subheader(f"日付: {analysis.get('date', '')}")

    results = analysis.get("results", [])

    # テーブル表示用
    table_data = []

    for r in results:
        table_data.append({
            "銘柄": r.get("symbol", ""),
            "判断": r.get("decision", ""),
            "理由": r.get("reason", ""),
            "学習ポイント": r.get("education", ""),
            "現在株価": r.get("today_price", "")
        })

    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True)

    st.divider()

    # 個別詳細表示
    st.subheader("📈 詳細チャート")

    for r in results:
        st.markdown(f"### {r['symbol']}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**判断**")
            st.success(r["decision"])

            st.write("**理由**")
            st.write(r["reason"])

        with col2:
            st.write("**学習ポイント**")
            st.info(r["education"])

            st.write("**現在価格**")
            st.write(r.get("today_price", ""))

        st.divider()
# ---------- フィードバック ----------
st.header("フィードバック")
fb = st.text_area("実際どうでしたか？")

if st.button("フィードバック送信"):
    json.dump({"feedback": fb}, open("feedback.json", "w", encoding="utf-8"), ensure_ascii=False)
    st.success("保存")
