from flask import Flask, request, jsonify, render_template
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  # 讓 JSON 正常顯示中文


# ---- 核心分析函式 ----
def analyze_stock_yf(symbol: str):
    # 抓最近 3 個月的日線資料，自動還原股價
    data = yf.download(
        symbol,
        period="3mo",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if data is None or data.empty:
        raise ValueError("查無資料")

    closes = data["Close"].dropna()
    volumes = data["Volume"].dropna()

    if len(closes) < 2:
        raise ValueError("資料筆數不足，無法分析")

    latest_close = float(closes.iloc[-1])
    prev_close = float(closes.iloc[-2])

    ma5 = float(closes.rolling(5).mean().iloc[-1])
    ma20 = float(closes.rolling(20).mean().iloc[-1])
    volume = int(volumes.iloc[-1])

    change_pct = round((latest_close - prev_close) / prev_close * 100, 2)

    result = {
        "最新價格": round(latest_close, 2),
        "昨收": round(prev_close, 2),
        "漲跌幅": change_pct,
        "MA5": round(ma5, 2),
        "MA20": round(ma20, 2),
        "成交量": volume,
    }

    # 趨勢判斷
    if ma5 > ma20:
        result["趨勢分析"] = "多頭趨勢"
    elif ma5 < ma20:
        result["趨勢分析"] = "空頭趨勢"
    else:
        result["趨勢分析"] = "整理盤"

    return result


# ---- 首頁：武吉拉畫面 ----
@app.route("/")
def index():
    return render_template("index.html")


# ---- API：查股票 ----
@app.route("/api/stock", methods=["GET"])
def api_stock():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "請輸入股票代碼"}), 400

    symbol = symbol.strip()

    try:
        result = analyze_stock_yf(symbol)
        return jsonify({"股票": symbol, "分析": result})
    except Exception as e:
        return jsonify({"error": f"查詢失敗：{str(e)}"}), 500


if __name__ == "__main__":
    # 讓區網內手機也能用：host="0.0.0.0"
    app.run(host="0.0.0.0", port=5000, debug=True)
