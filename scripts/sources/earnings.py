"""トヨタ自動車の決算ダイジェスト(公式IRサイト)。

https://global.toyota/jp/ir/financial-results/ (静的HTML、認証不要)から
最新の決算リリース(決算要旨PDF)を、
https://global.toyota/jp/ir/financial-results/archives/03.html から
直近の通期(四半期でない)決算リリースを特定し、それぞれのPDF本文を
pdfplumberでテキスト抽出して以下を取得する:

  - quarterly: 最新四半期の連結業績(3ヶ月)と前年同期比
  - full_year.prior_actual: 直近に確定した通期(全年度)実績
  - full_year.initial_forecast: その通期実績と同時に発表された、
    新年度に対する「期初」の通期業績予想
  - full_year.latest_forecast: 最新の四半期決算で更新された、
    現在の通期業績予想(「最新」の見通し)

トヨタの決算短信はIFRS基準のため、日本基準の「経常利益」は存在せず、
代わりに「税引前利益」を掲載する。単位は百万円。

PDF構造は2026-09-05に実際のPDF(2027_1q_summary_jp.pdf, 2026_4q_summary_jp.pdf)
で確認済み。全角数字が混在するためunicodedata.normalize("NFKC", ...)で
半角化してから正規表現で抽出する。
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
ARCHIVE_URL = "https://global.toyota/jp/ir/financial-results/archives/03.html"

# (1)連結経営成績の行: 決算期ラベル + 6指標×(実数, 前年(同期)比%)。
# PDFのテキスト抽出では、実数とその直後の(マイナス表記の)前年比%との間に
# 空白が入らないことがある(例: "3,766,216-21.5")ため、値と%の間は\s*で許容する。
_ROW_PATTERN = re.compile(r"(\d{4}年\d{1,2}月期(?:第\d四半期)?)((?:\s+-?[\d,]+\.?\d*\s*-?[\d.]+){6})")
# 3.通期業績予想の行: 「通期」+ 4指標×(実数, 前期比%) + 基本的EPS(実数のみ)
_FORECAST_PATTERN = re.compile(
    r"通期"
    r"\s+(-?[\d,]+)\s*(-?[\d.]+)"
    r"\s+(-?[\d,]+)\s*(-?[\d.]+)"
    r"\s+(-?[\d,]+)\s*(-?[\d.]+)"
    r"\s+(-?[\d,]+)\s*(-?[\d.]+)"
    r"\s+([\d.]+)"
)
_EPS_PATTERN = re.compile(r"(\d{4}年\d{1,2}月期(?:第\d四半期)?)\s+([\d.]+)\s+([\d.]+)")

_ACTUAL_METRIC_KEYS = [
    "revenue",
    "operating_income",
    "income_before_tax",
    "profit_before_attribution",
    "net_income",
    "comprehensive_income",
]
_FORECAST_METRIC_KEYS = ["revenue", "operating_income", "income_before_tax", "net_income"]


def _to_number(text: str) -> float | None:
    text = (text or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _find_pdf_link_by_text(soup: BeautifulSoup, link_text: str, scope=None) -> str | None:
    root = scope if scope is not None else soup
    for a in root.find_all("a"):
        if a.get_text(strip=True) == link_text:
            href = a.get("href")
            if not href:
                continue
            return "https://global.toyota" + href if href.startswith("/") else href
    return None


def _find_latest_release(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    period_heading = soup.select_one("h2.title")
    quarter_heading = soup.select_one("h3.title")
    if quarter_heading is None:
        return None
    pdf_url = _find_pdf_link_by_text(soup, "決算要旨")
    if pdf_url is None:
        return None
    title = ((period_heading.get_text(strip=True) if period_heading else "") + " " + quarter_heading.get_text(strip=True)).strip()
    return {"title": title, "pdf_url": pdf_url}


def _find_latest_annual_release(html: str) -> dict | None:
    """アーカイブページから直近の通期(「第N四半期」を含まない)決算要旨を探す。"""
    soup = BeautifulSoup(html, "html.parser")
    for h3 in soup.select("h3.title"):
        heading = h3.get_text(strip=True)
        if not heading.startswith("決算情報"):
            continue
        ul = h3.find_next("ul")
        if ul is None:
            continue
        pdf_url = _find_pdf_link_by_text(soup, "決算要旨", scope=ul)
        if pdf_url is None:
            continue
        h2 = h3.find_previous("h2", class_="title")
        title = ((h2.get_text(strip=True) if h2 else "") + " " + heading).strip()
        return {"title": title, "pdf_url": pdf_url}
    return None


def _extract_pdf_data(pdf_bytes: bytes) -> dict:
    """1つのPDFから、当該リリースの実績(actual)と通期予想(forecast)を抽出する。"""
    result: dict = {"actual": None, "forecast": None, "announced": None}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            normalized = unicodedata.normalize("NFKC", text).replace("△", "-")

            if result["announced"] is None:
                m = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", normalized)
                if m:
                    result["announced"] = m.group(1)

            if result["actual"] is None:
                matches = _ROW_PATTERN.findall(normalized)
                if matches:
                    period_label, nums_text = matches[0]
                    nums = [_to_number(n) for n in re.findall(r"-?[\d,.]+", nums_text)]
                    metrics: dict = {}
                    for i, key in enumerate(_ACTUAL_METRIC_KEYS):
                        metrics[key] = nums[i * 2]
                        metrics[key + "_yoy"] = nums[i * 2 + 1]

                    eps_basic = None
                    eps_idx = normalized.find("基本的1株当たり")
                    if eps_idx >= 0:
                        eps_match = _EPS_PATTERN.search(normalized[eps_idx : eps_idx + 400])
                        if eps_match:
                            eps_basic = _to_number(eps_match.group(2))

                    operating_margin = None
                    if metrics.get("revenue") and metrics.get("operating_income") is not None:
                        operating_margin = round(metrics["operating_income"] / metrics["revenue"] * 100, 1)

                    result["actual"] = {
                        "period_label": period_label,
                        "eps": eps_basic,
                        "operating_margin": operating_margin,
                        **metrics,
                    }

            if result["forecast"] is None:
                fm = _FORECAST_PATTERN.search(normalized)
                if fm:
                    vals = [_to_number(g) for g in fm.groups()]
                    metrics = {}
                    for i, key in enumerate(_FORECAST_METRIC_KEYS):
                        metrics[key] = vals[i * 2]
                        metrics[key + "_yoy"] = vals[i * 2 + 1]
                    metrics["eps"] = vals[8]
                    result["forecast"] = metrics

            if result["actual"] and result["forecast"] and result["announced"]:
                break
    return result


def fetch() -> dict:
    try:
        resp = requests.get(PAGE_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        release = _find_latest_release(resp.text)
        if release is None:
            return {"quarterly": None, "full_year": None, "source_url": PAGE_URL, "error": "latest release not found"}

        pdf_resp = requests.get(release["pdf_url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        pdf_resp.raise_for_status()
        latest_data = _extract_pdf_data(pdf_resp.content)
        if latest_data["actual"] is None:
            return {"quarterly": None, "full_year": None, "source_url": PAGE_URL, "error": "could not parse latest PDF"}

        quarterly = {
            **latest_data["actual"],
            "announced": latest_data["announced"],
            "release_title": release["title"],
            "pdf_url": release["pdf_url"],
        }

        full_year = {
            "latest_forecast": latest_data["forecast"],
            "initial_forecast": None,
            "prior_actual": None,
            "prior_release_title": None,
            "prior_pdf_url": None,
        }

        try:
            archive_resp = requests.get(ARCHIVE_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            archive_resp.raise_for_status()
            annual_release = _find_latest_annual_release(archive_resp.text)
            if annual_release:
                annual_pdf_resp = requests.get(
                    annual_release["pdf_url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
                )
                annual_pdf_resp.raise_for_status()
                annual_data = _extract_pdf_data(annual_pdf_resp.content)
                full_year["prior_actual"] = annual_data["actual"]
                full_year["initial_forecast"] = annual_data["forecast"]
                full_year["prior_release_title"] = annual_release["title"]
                full_year["prior_pdf_url"] = annual_release["pdf_url"]
        except Exception:  # noqa: BLE001
            pass  # 通期比較は無くても四半期ダイジェストは表示できるため握りつぶす

        return {
            "quarterly": quarterly,
            "full_year": full_year,
            "unit": "百万円",
            "source_url": PAGE_URL,
            "source_label": "トヨタ自動車 投資家情報(公式)",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"quarterly": None, "full_year": None, "source_url": PAGE_URL, "error": str(exc)}
