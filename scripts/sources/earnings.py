"""トヨタ自動車の直近四半期(3ヶ月)決算ダイジェスト。

株探(kabutan.jp)の業績推移ページ(静的HTML、認証不要)から、直近の四半期
(3ヶ月)決算の売上高・営業利益・経常利益・最終利益・EPS・売上営業利益率と
前年同期比(%)を取得する。非公式の第三者集計サイトであり、正式な数値は
トヨタ自動車の決算短信(IR資料)を参照のこと。単位はいずれも百万円。

ページ構造は2026-09-05にcurlで直接確認: `.fin_quarter_result_d table` が
3ヶ月決算の実績テーブルで、各行が決算期(例: "26.04-06")ごとの
売上高/営業益/経常益/最終益/修正1株益/売上営業損益率/発表日を持ち、
末尾に前年同期比(%)の行が続く。
"""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .common import REQUEST_TIMEOUT

URL = "https://kabutan.jp/stock/finance?code=7203"

# kabutan.jpは自己申告のbot UA(User-Agentに"Bot"等を含む文字列)を403で拒否するため、
# このスクレイパーのみ一般的なブラウザUAを用いる(2026-09-05に確認)。
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

_YOY_KEYS = ["revenue", "operating_income", "ordinary_income", "net_income", "eps"]


def _parse_number(text: str) -> float | None:
    text = (text or "").strip().replace(",", "").replace("+", "")
    if not text or text in ("－", "-", "―", "&nbsp;"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch() -> dict:
    try:
        resp = requests.get(URL, headers={"User-Agent": _BROWSER_USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one(".fin_quarter_result_d table")
        if table is None:
            return {"latest": None, "source_url": URL, "error": "quarterly table not found"}

        data_rows: list[tuple[str, list[str]]] = []
        yoy_cells: list[str] | None = None
        for row in table.select("tbody tr"):
            header = row.select_one("th")
            if header is None:
                continue
            # <th>には区分記号(kubun1スパン、例: "I")と決算期(例: "26.04-06")が
            # 連結されて入っているため、決算期部分のみを正規表現で抜き出す。
            raw_label = header.get_text(strip=True)
            period_match = re.search(r"\d{2}\.\d{2}-\d{2}", raw_label)
            label = period_match.group(0) if period_match else raw_label
            cells = [c.get_text(strip=True) for c in row.select("td")]
            if label == "前年同期比":
                yoy_cells = cells
                continue
            if len(cells) < 7:
                continue
            data_rows.append((label, cells))

        if not data_rows:
            return {"latest": None, "source_url": URL, "error": "no quarterly data rows found"}

        period_label, cells = data_rows[-1]
        announced_match = re.search(r"\d{2}/\d{2}/\d{2}", cells[6])

        display_label = period_label
        ym_match = re.match(r"(\d{2})\.(\d{2})-(\d{2})", period_label)
        if ym_match:
            yy, month_start, month_end = ym_match.groups()
            display_label = f"20{yy}年{int(month_start)}-{int(month_end)}月期"

        latest = {
            "period_label": display_label,
            "revenue": _parse_number(cells[0]),
            "operating_income": _parse_number(cells[1]),
            "ordinary_income": _parse_number(cells[2]),
            "net_income": _parse_number(cells[3]),
            "eps": _parse_number(cells[4]),
            "operating_margin": _parse_number(cells[5]),
            "announced": announced_match.group(0) if announced_match else None,
            "yoy": {},
        }

        if yoy_cells and len(yoy_cells) >= 5:
            for key, val in zip(_YOY_KEYS, yoy_cells[:5]):
                latest["yoy"][key] = _parse_number(val)

        return {
            "latest": latest,
            "unit": "百万円",
            "source_url": URL,
            "source_label": "株探(kabutan.jp)",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"latest": None, "source_url": URL, "error": str(exc)}
