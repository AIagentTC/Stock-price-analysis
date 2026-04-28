import streamlit as st
import json
import os
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI株式アシスタント", layout="wide")
st.title("📈 AI株式アシスタント")

# ---------- 読み込み ----------
if os.path.exists("data.json"):
    data = json.load(open("data.json", "r", encoding="utf-8"))
else:
    data = {"symbols": [], "extra_news": []}

# ---------- 銘柄追加 ----------
st.header("銘柄追加")
symbol = st.text_input("銘柄コード（例: 7203.T）")

if st.button("追加"):
    info = yf.Ticker(symbol).info
    name = info.get("longName", "不明")
    data["symbols"].append(symbol)
    json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    st.success(f"{name} を追加")

# ---------- ニュース ----------
st.header("ニュース追加")
news = st.text_area("AIに教えたい材料")

if st.button("保存"):
    data["extra_news"].append(news)
    json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    st.success("保存")

# ---------- 結果表示 ----------
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