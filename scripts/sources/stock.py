"""トヨタ自動車(7203.T)の株価データ。

Yahoo FinanceのチャートAPI(v8/finance/chart)はAPIキー不要・無認証で
利用できる公開エンドポイントであるため、これを用いて直近3ヶ月の日次終値と
当日の株価サマリーを取得する。非公式エンドポイントのため、構造変化や
レート制限により取得できなくなる場合がある。
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

SYMBOL = "7203.T"
URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}"


def fetch() -> dict:
    try:
        resp = requests.get(
            URL,
            params={"range": "3mo", "interval": "1d"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", []) or []
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", []) or []

        history = []
        for ts, close in zip(timestamps, closes):
            if close is None:
                continue
            date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            history.append({"date": date, "close": round(close, 1)})

        return {
            "symbol": SYMBOL,
            "currency": meta.get("currency", "JPY"),
            "price": meta.get("regularMarketPrice"),
            "change": meta.get("fulldayChange"),
            "change_percent": meta.get("fulldayChangePercent"),
            "previous_close": meta.get("chartPreviousClose"),
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "history": history,
            "source_url": "https://finance.yahoo.com/quote/7203.T/",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"symbol": SYMBOL, "history": [], "error": str(exc)}
