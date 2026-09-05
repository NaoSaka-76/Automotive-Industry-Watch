"""トヨタ自動車の直近決算ダイジェスト(公式IRサイト)。

https://global.toyota/jp/ir/financial-results/ (静的HTML、認証不要)から
最新の決算リリース(決算要旨PDF)を特定し、PDF本文をpdfplumberでテキスト抽出、
連結業績の主要数値(営業収益・営業利益・税引前四半期利益・親会社所有者帰属
四半期利益・EPS)と前年同期比(%)を取得する。トヨタの決算短信はIFRS基準の
ため、日本基準でよく使われる「経常利益」の概念はなく、代わりに「税引前
四半期利益」を掲載する。単位は百万円。

PDF構造は2026-09-05に実際のPDF(2027_1q_summary_jp.pdf)で確認済み:
1ページ目に決算期のタイトル、2ページ目(以降)に
「(1)連結経営成績(累計)」の表があり、当期・前年同期の2行に
6指標×(実数, 前年同期比%)が並ぶ。全角数字が混在するため
unicodedata.normalize("NFKC", ...)で半角化してから正規表現で抽出する。
"""

from __future__ import annotations

import io
import re
import unicodedata

import pdfplumber
import requests
from bs4 import BeautifulSoup

from .common import REQUEST_TIMEOUT, USER_AGENT

PAGE_URL = "https://global.toyota/jp/ir/financial-results/"

_ROW_PATTERN = re.compile(r"(\d{4}年\d{1,2}月期第?\d?四半期?)((?:\s+-?[\d,]+\.?\d*\s+-?[\d.]+){6})")
_EPS_PATTERN = re.compile(r"(\d{4}年\d{1,2}月期第?\d?四半期?)\s+([\d.]+)\s+([\d.]+)")

_METRIC_KEYS = [
    "revenue",
    "operating_income",
    "income_before_tax",
    "quarterly_profit",
    "net_income",
    "comprehensive_income",
]


def _to_number(text: str) -> float | None:
    text = text.replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _find_latest_release(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    period_heading = soup.select_one("h2.title")
    quarter_heading = soup.select_one("h3.title")
    pdf_link = None
    for a in soup.select("a.ico_pdf"):
        if "決算要旨" in a.get_text():
            pdf_link = a.get("href")
            break
    if pdf_link is None:
        return None
    if pdf_link.startswith("/"):
        pdf_link = "https://global.toyota" + pdf_link

    release_title = (period_heading.get_text(strip=True) if period_heading else "") + " " + (
        quarter_heading.get_text(strip=True) if quarter_heading else ""
    )
    return {"title": release_title.strip(), "pdf_url": pdf_link}


def _parse_pdf(pdf_bytes: bytes) -> dict | None:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            normalized = unicodedata.normalize("NFKC", text).replace("△", "-")
            matches = _ROW_PATTERN.findall(normalized)
            if not matches:
                continue

            period_label, nums_text = matches[0]
            nums = re.findall(r"-?[\d,.]+", nums_text)
            values = [_to_number(n) for n in nums]
            metrics = {}
            for i, key in enumerate(_METRIC_KEYS):
                metrics[key] = values[i * 2]
                metrics[key + "_yoy"] = values[i * 2 + 1]

            eps_basic = None
            eps_idx = normalized.find("基本的1株当たり")
            if eps_idx >= 0:
                eps_match = _EPS_PATTERN.search(normalized[eps_idx : eps_idx + 400])
                if eps_match:
                    eps_basic = _to_number(eps_match.group(2))

            announced_match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", normalized)

            operating_margin = None
            if metrics.get("revenue") and metrics.get("operating_income") is not None:
                operating_margin = round(metrics["operating_income"] / metrics["revenue"] * 100, 1)

            return {
                "period_label": period_label,
                "announced": announced_match.group(1) if announced_match else None,
                "eps": eps_basic,
                "operating_margin": operating_margin,
                **metrics,
            }
    return None


def fetch() -> dict:
    try:
        resp = requests.get(PAGE_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        release = _find_latest_release(resp.text)
        if release is None:
            return {"latest": None, "source_url": PAGE_URL, "error": "latest release PDF link not found"}

        pdf_resp = requests.get(release["pdf_url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        pdf_resp.raise_for_status()
        parsed = _parse_pdf(pdf_resp.content)
        if parsed is None:
            return {"latest": None, "source_url": PAGE_URL, "error": "could not parse figures from PDF"}

        parsed["release_title"] = release["title"]
        parsed["pdf_url"] = release["pdf_url"]

        return {
            "latest": parsed,
            "unit": "百万円",
            "source_url": PAGE_URL,
            "source_label": "トヨタ自動車 投資家情報(公式)",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"latest": None, "source_url": PAGE_URL, "error": str(exc)}
