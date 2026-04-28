import json
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ---------- データ読み込み ----------
with open("data.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

with open("feedback.json", "r", encoding="utf-8") as f:
    feedback = json.load(f)["feedback"]

symbols = user_data["symbols"]
extra_news = user_data["extra_news"]

results = []

for symbol in symbols:
    df = yf.download(symbol, period="3mo")
    df.dropna(inplace=True)

    rsi = RSIIndicator(df["Close"]).rsi().iloc[-1]
    macd = MACD(df["Close"]).macd_diff().iloc[-1]

    chart_data = [
        {"date": str(i.date()), "close": float(c)}
        for i, c in zip(df.index, df["Close"])
    ]

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
1. 売るべきか保有か買い増しかの結論
2. テクニカル＋ニュースの理由
3. 初心者向けの学習ポイント
"""

    res = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
    )

    text = res.choices[0].message.content.split("\n")

    results.append({
        "symbol": symbol,
        "decision": text[0],
        "reason": text[1] if len(text) > 1 else "",
        "education": text[2] if len(text) > 2 else "",
        "chart": chart_data
    })

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)