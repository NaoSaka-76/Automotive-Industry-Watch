"""トヨタ自動車(7203.T)の株価データ。

Yahoo FinanceのチャートAPI(v8/finance/chart)はAPIキー不要・無認証で
利用できる公開エンドポイントであるため、これを用いて株価を取得する。
非公式エンドポイントのため、構造変化やレート制限により取得できなくなる
場合がある。

フロントエンド側で 日/週/月/3ヶ月/6ヶ月/1年 の期間切替を行えるよう、
2種類の粒度でヒストリカルデータを取得しておく:
  - intraday: 直近5営業日・15分足(「日」「週」表示の元データ)
  - daily: 直近1年・日足(「月」「3ヶ月」「6ヶ月」「1年」表示の元データ、
    フロントエンド側で期間分だけ末尾を切り出す)
"""

from __future__ import annotations

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

SYMBOL = "7203.T"
URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}"


def _fetch_series(range_: str, interval: str) -> list[dict]:
    resp = requests.get(
        URL,
        params={"range": range_, "interval": interval},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result.get("timestamp", []) or []
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", []) or []

    points = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        points.append({"t": int(ts), "close": round(close, 1)})
    return points


def fetch() -> dict:
    try:
        # metaは日足取得のレスポンスから取る(当日の現在値・前日比等)。
        resp = requests.get(
            URL,
            params={"range": "1y", "interval": "1d"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", []) or []
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", []) or []
        daily = [
            {"t": int(ts), "close": round(c, 1)}
            for ts, c in zip(timestamps, closes)
            if c is not None
        ]

        intraday: list[dict] = []
        try:
            intraday = _fetch_series("5d", "15m")
        except Exception:  # noqa: BLE001
            intraday = []

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
            "daily": daily,
            "intraday": intraday,
            "source_url": "https://finance.yahoo.com/quote/7203.T/",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"symbol": SYMBOL, "daily": [], "intraday": [], "error": str(exc)}
