"""トヨタ以外の日本の主要自動車メーカーの株価(比較チャート用)。

トヨタ自身の当日サマリー(現在値・前日比等)はstock.pyが取得しているため、
ここではチャート描画に必要な日足(1年)・分足(直近5営業日)の時系列のみを
他メーカー分取得する。Yahoo Financeの無料・無認証チャートAPIを使用。
"""

from __future__ import annotations

from .stock import fetch_series

PEERS = [
    {"key": "honda", "label": "ホンダ", "symbol": "7267.T"},
    {"key": "nissan", "label": "日産自動車", "symbol": "7201.T"},
    {"key": "suzuki", "label": "スズキ", "symbol": "7269.T"},
    {"key": "mazda", "label": "マツダ", "symbol": "7261.T"},
    {"key": "subaru", "label": "SUBARU", "symbol": "7270.T"},
    {"key": "mitsubishi", "label": "三菱自動車", "symbol": "7211.T"},
]


def fetch() -> dict:
    result: dict = {}
    for peer in PEERS:
        try:
            daily = fetch_series(peer["symbol"], "1y", "1d")
        except Exception:  # noqa: BLE001
            daily = []
        try:
            intraday = fetch_series(peer["symbol"], "5d", "15m")
        except Exception:  # noqa: BLE001
            intraday = []
        result[peer["key"]] = {
            "label": peer["label"],
            "symbol": peer["symbol"],
            "daily": daily,
            "intraday": intraday,
        }
    return result
