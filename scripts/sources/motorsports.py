"""モータースポーツ カテゴリー別トピックス。

対象カテゴリー(9): F1 / WEC・ル・マン(耐久) / WRC・ラリー / NASCAR・IndyCar(北米) /
Super GT・スーパーフォーミュラ(国内) / Formula E(電動) / クロスカントリーラリー
(ダカールラリー等) / ドリフト(D1GP等) / 全日本ラリー選手権(国内ラリー)。

ニュース速報の収集のみを対象とし、日程・ランキングのスクレイピングは行わない
(要件外のため)。
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency, sort_by_relevance

CATEGORIES: dict[str, dict] = {
    "f1": {
        "label": "F1",
        "queries": [
            ("\"Formula 1\" OR F1", "en-US", "US", "US:en"),
            ("F1 OR フォーミュラ1", "ja", "JP", "JP:ja"),
        ],
    },
    "wec": {
        "label": "WEC・ル・マン(耐久)",
        "queries": [
            ("WEC OR \"World Endurance Championship\" OR \"24 Hours of Le Mans\"", "en-US", "US", "US:en"),
            ("WEC OR 世界耐久選手権 OR ルマン24時間", "ja", "JP", "JP:ja"),
        ],
    },
    "wrc": {
        "label": "WRC・ラリー",
        "queries": [
            ("WRC OR \"World Rally Championship\"", "en-US", "US", "US:en"),
            ("WRC OR 世界ラリー選手権", "ja", "JP", "JP:ja"),
        ],
    },
    "nascar_indycar": {
        "label": "NASCAR・IndyCar(北米)",
        "queries": [
            ("NASCAR (race OR championship)", "en-US", "US", "US:en"),
            ("IndyCar (race OR championship)", "en-US", "US", "US:en"),
        ],
    },
    "super_gt_sf": {
        "label": "Super GT・スーパーフォーミュラ(国内)",
        "queries": [
            ("SUPER GT スーパーGT", "ja", "JP", "JP:ja"),
            ("スーパーフォーミュラ SUPER FORMULA", "ja", "JP", "JP:ja"),
        ],
    },
    "formula_e": {
        "label": "Formula E(電動)",
        "queries": [
            ("\"Formula E\" (race OR championship)", "en-US", "US", "US:en"),
            ("フォーミュラE 電動レース", "ja", "JP", "JP:ja"),
        ],
    },
    "cross_country_rally": {
        "label": "クロスカントリーラリー(ダカール等)",
        "queries": [
            ("Dakar Rally", "en-US", "US", "US:en"),
            ("ダカールラリー", "ja", "JP", "JP:ja"),
            ("cross-country rally championship W2RC", "en-US", "US", "US:en"),
        ],
    },
    "drift": {
        "label": "ドリフト(D1GP等)",
        "queries": [
            ("D1GP OR \"D1グランプリ\"", "ja", "JP", "JP:ja"),
            ("Formula Drift", "en-US", "US", "US:en"),
        ],
    },
    "all_japan_rally": {
        "label": "全日本ラリー選手権(国内)",
        "queries": [
            ("全日本ラリー選手権", "ja", "JP", "JP:ja"),
            ("JAF全日本ラリー", "ja", "JP", "JP:ja"),
        ],
    },
}


def _fetch_category(queries: list[tuple], limit_per_query: int = 10) -> dict:
    raw: list[dict] = []
    for query, hl, gl, ceid in queries:
        results = fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query)
        for r in results:
            r["_query_key"] = query
        raw.extend(results)

    deduped = dedupe_by_url(raw)
    newest = sort_by_recency(deduped)
    popular = sort_by_relevance(deduped)
    return {"newest": newest, "popular": popular}


def fetch() -> dict:
    return {key: {"label": c["label"], **_fetch_category(c["queries"])} for key, c in CATEGORIES.items()}
