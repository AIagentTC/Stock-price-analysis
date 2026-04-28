import json
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from openai import OpenAI
import os
from datetime import datetime

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# =====================================================
# 🔧 安全JSONロード（追加）
# =====================================================
def safe_json_load(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# =====================================================
# データ読み込み
# =====================================================
with open("data.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

with open("feedback.json", "r", encoding="utf-8") as f:
    feedback = json.load(f).get("feedback", "")

symbols = user_data.get("symbols", [])
extra_news = user_data.get("extra_news", [])

results = []

# =====================================================
# 株分析
# =====================================================
for symbol in symbols:

    try:
        df = yf.download(symbol, period="3mo")

        if df is None or df.empty:
            continue

        # Close安全化
        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce").dropna().squeeze()

        if len(close) < 30:
            continue

        # 指標
        rsi = RSIIndicator(close).rsi().iloc[-1]
        macd = MACD(close).macd_diff().iloc[-1]

        # チャート
        chart_data = [
            {"date": str(i.date()), "close": float(c)}
            for i, c in zip(df.index[-len(close):], close)
        ]

        # AI
        prompt = f"""
あなたはプロの株式アナリストです。

銘柄: {symbol}
RSI: {rsi}
MACD差分: {macd}

ユーザー追加ニュース:
{extra_news}

過去フィードバック:
{feedback}

以下をJSON形式で出力してください：

{{
  "decision": "売る/保有/買い増しのいずれか",
  "reason": "理由",
  "education": "学習ポイント"
}}
"""

        res = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
        )

        content = res.choices[0].message.content
        content = content.strip().replace("```json", "").replace("```", "")

        parsed = json.loads(content)

        results.append({
            "symbol": symbol,
            "decision": parsed.get("decision", ""),
            "reason": parsed.get("reason", ""),
            "education": parsed.get("education", ""),
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

# =====================================================
# ① Result（最新）
# =====================================================
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# =====================================================
# ② Analysis Today
# =====================================================
analysis_today = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "results": results
}

with open("analysis_today.json", "w", encoding="utf-8") as f:
    json.dump(analysis_today, f, ensure_ascii=False, indent=2)

# =====================================================
# ③ Analysis History（安全追記）
# =====================================================
history_file = "analysis_history.json"

history = safe_json_load(history_file)

history.append(analysis_today)

with open(history_file, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
