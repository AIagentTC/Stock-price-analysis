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
# 安全JSONロード
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

# =====================================================
# コンテナ分離
# =====================================================
result_only = []          # ① 3ヶ月データ＋指標
analysis_today = []       # ② 今日の分析＋当日株価

# =====================================================
# 株分析
# =====================================================
for symbol in symbols:

    try:
        df = yf.download(symbol, period="3mo")

        if df is None or df.empty:
            continue

        # -------------------------
        # Close安全化
        # -------------------------
        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce").dropna().squeeze()

        if len(close) < 30:
            continue

        # -------------------------
        # テクニカル指標（3ヶ月データベース）
        # -------------------------
        rsi = RSIIndicator(close).rsi().iloc[-1]
        macd = MACD(close).macd_diff().iloc[-1]

        # =====================================================
        # ① RESULT用（3ヶ月データ＋指標のみ）
        # =====================================================
        result_only.append({
            "symbol": symbol,
            "rsi": float(rsi),
            "macd": float(macd),
            "price_history": [
                {"date": str(i.date()), "close": float(c)}
                for i, c in zip(df.index[-len(close):], close)
            ]
        })

        # =====================================================
        # AIプロンプト（3ヶ月データを元に分析）
        # =====================================================
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

        content = res.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")

        parsed = json.loads(content)

        # =====================================================
        # ② ANALYSIS TODAY（軽量＋当日価格）
        # =====================================================
        analysis_today.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "symbol": symbol,
            "decision": parsed.get("decision", ""),
            "reason": parsed.get("reason", ""),
            "education": parsed.get("education", ""),
            "today_price": float(close.iloc[-1])  # 最新価格のみ
        })

    except Exception as e:

        result_only.append({
            "symbol": symbol,
            "error": str(e)
        })

        analysis_today.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "symbol": symbol,
            "decision": "エラー",
            "reason": str(e),
            "education": "",
            "today_price": None
        })

# =====================================================
# ① result.json（3ヶ月データ＋指標）
# =====================================================
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result_only, f, ensure_ascii=False, indent=2)

# =====================================================
# ② analysis_today.json（当日結果のみ）
# =====================================================
with open("analysis_today.json", "w", encoding="utf-8") as f:
    json.dump(analysis_today, f, ensure_ascii=False, indent=2)

# =====================================================
# ③ analysis_history.json（蓄積）
# =====================================================
history_file = "analysis_history.json"
history = safe_json_load(history_file)

history.append({
    "date": datetime.now().strftime("%Y-%m-%d"),
    "results": analysis_today   # ←そのままlistを入れる
})

with open(history_file, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
