import json
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("data.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

with open("feedback.json", "r", encoding="utf-8") as f:
    feedback = json.load(f).get("feedback", "")

symbols = user_data.get("symbols", [])
extra_news = user_data.get("extra_news", [])

results = []

for symbol in symbols:

    try:
        df = yf.download(symbol, period="3mo")

        if df is None or df.empty:
            continue

        # ===== 🔥 Closeを完全に1次元化（ここが最重要） =====
        close = df["Close"]

        # DataFrame化対策
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce")
        close = close.dropna().squeeze()

        # データ不足ガード
        if len(close) < 30:
            continue

        # ===== テクニカル指標 =====
        rsi_series = RSIIndicator(close)
        macd_series = MACD(close)

        rsi = rsi_series.rsi().iloc[-1]
        macd = macd_series.macd_diff().iloc[-1]

        # ===== チャート =====
        chart_data = [
            {"date": str(i.date()), "close": float(c)}
            for i, c in zip(df.index[-len(close):], close)
        ]

        # ===== AIプロンプト =====
        prompt = f"""
あなたはプロの株式アナリストです。

銘柄: {symbol}
RSI: {rsi}
MACD差分: {macd}

ユーザー追加ニュース:
{extra_news}

過去フィードバック:
{feedback}

以下を日本語で出力してください:
1. 売るべきか保有か買い増しか
2. 理由
3. 学習ポイント
"""

        res = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
        )

        text = res.choices[0].message.content.split("\n")

        results.append({
            "symbol": symbol,
            "decision": text[0] if len(text) > 0 else "",
            "reason": text[1] if len(text) > 1 else "",
            "education": text[2] if len(text) > 2 else "",
            "chart": chart_data
        })

    except Exception as e:
        results.append({
            "symbol": symbol,
            "decision": "エラー",
            "reason": str(e),
            "education": "",
            "chart": []
        })

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
