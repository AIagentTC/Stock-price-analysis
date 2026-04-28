import streamlit as st
import json
import os
import requests
import base64
import pandas as pd

st.set_page_config(page_title="AI株式アシスタント", layout="wide")
st.title("📈 AI株式アシスタント")

# =====================================================
# タブ分割
# =====================================================
tab1, tab2 = st.tabs(["📥 入力", "📊 分析結果"])

# =====================================================
# GitHub設定
# =====================================================
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]

DATA_PATH = "data.json"
GITHUB_API = f"https://api.github.com/repos/{REPO}/contents/{DATA_PATH}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------- GitHubからdata.json取得 ----------
def load_data():
    r = requests.get(GITHUB_API, headers=headers)
    r.raise_for_status()

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

# =====================================================
# データ読み込み
# =====================================================
data, sha = load_data()

# =====================================================
# タブ①：入力画面
# =====================================================
with tab1:
    st.header("銘柄追加")
    symbol = st.text_input("銘柄コード（例: 7203.T）")

    if st.button("追加"):
        if symbol and symbol not in data["symbols"]:
            data["symbols"].append(symbol)
            save_data(data, sha)
            st.success(f"{symbol} を追加しました")
        else:
            st.warning("入力が空 or 既に登録済みです")

    st.header("ニュース追加")
    news = st.text_area("AIに教えたい材料")

    if st.button("保存"):
        if news:
            data["extra_news"].append(news)
            save_data(data, sha)
            st.success("保存しました")

# =====================================================
# タブ②：分析結果（analysis_today）
# =====================================================
with tab2:
    st.header("AI分析結果（本日）")

    if not os.path.exists("analysis_today.json"):
        st.warning("analysis_today.json が存在しません（GitHubに未反映の可能性）")
        st.stop()

    with open("analysis_today.json", "r", encoding="utf-8") as f:
        analysis = json.load(f)

    # list / dict 両対応
    if isinstance(analysis, list):
        analysis = analysis[-1] if analysis else {}

    results = analysis.get("results")

    # 🔥 ここが重要（None対策）
    if not results:
        st.warning("analysis_today.json は存在しますが results が空です")
        st.write(analysis)   # デバッグ表示
        st.stop()

    for r in results:
        st.subheader(r.get("symbol", "不明"))
        st.write("結論:", r.get("decision", ""))
        st.write("理由:", r.get("reason", ""))
        st.info(r.get("education", ""))

        if r.get("chart"):
            df = pd.DataFrame(r["chart"])
            st.line_chart(df.set_index("date")["close"])
