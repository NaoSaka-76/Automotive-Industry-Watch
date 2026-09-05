"""自動車産業に関するトピックス(地域別)。

地域: グローバル(global) / 日本 / アメリカ / ヨーロッパ / アジア / オセアニア /
アフリカ / 中東 / ロシア。

設計上の割り切り: 日本のみ日本語クエリを使用し、それ以外の地域はすべて英語
クエリ(地域ごとのGoogle Newsエディション + 地域名を含む検索語)で収集する。
ロシア語・ドイツ語・フランス語・アラビア語等の現地語クエリは対象外とし、
英語で報じられた国際ニュースのみを対象とする(カテゴリ分類キーワード辞書を
日英2言語に限定して保守可能な範囲に収めるため)。この点はUI注記に明記する。
"""

from __future__ import annotations

from .categorize import attach_category
from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency, sort_by_relevance
from .translate import attach_translations

# 各地域: (表示名, 絵文字, [(query, hl, gl, ceid), ...])
REGIONS: dict[str, dict] = {
    "global": {
        "label": "グローバル",
        "flag": "🌍",
        "queries": [
            ("global automotive industry", "en-US", "US", "US:en"),
            ("automaker OR automakers news", "en-US", "US", "US:en"),
            ("EV market OR electric vehicle industry", "en-US", "US", "US:en"),
            ("自動車業界 グローバル", "ja", "JP", "JP:ja"),
        ],
    },
    "japan": {
        "label": "日本",
        "flag": "🇯🇵",
        "queries": [
            ("自動車業界 OR 自動車メーカー", "ja", "JP", "JP:ja"),
            ("自動車 (新型 OR 発表 OR 決算 OR 生産)", "ja", "JP", "JP:ja"),
            ("EV 電気自動車 日本 自動車メーカー", "ja", "JP", "JP:ja"),
            ("自動車 (経済産業省 OR 排出ガス規制 OR 補助金)", "ja", "JP", "JP:ja"),
        ],
    },
    "us": {
        "label": "アメリカ",
        "flag": "🇺🇸",
        "queries": [
            ("US automotive industry OR US automakers", "en-US", "US", "US:en"),
            ("Detroit automaker OR \"Big Three\" automotive", "en-US", "US", "US:en"),
            ("EV market United States automaker", "en-US", "US", "US:en"),
            ("automotive tariff OR regulation United States", "en-US", "US", "US:en"),
        ],
    },
    "europe": {
        "label": "ヨーロッパ",
        "flag": "🇪🇺",
        "queries": [
            ("European automotive industry OR European automakers", "en-GB", "GB", "GB:en"),
            ("EU automotive regulation OR emissions rule", "en-GB", "GB", "GB:en"),
            ("German automaker OR French automaker OR European carmaker", "en-GB", "GB", "GB:en"),
            ("EU EV market OR European electric vehicle", "en-GB", "GB", "GB:en"),
        ],
    },
    "asia": {
        "label": "アジア",
        "flag": "🌏",
        "queries": [
            ("China automotive industry OR Chinese automaker", "en-US", "US", "US:en"),
            ("South Korea automaker OR Korean automotive industry", "en-US", "US", "US:en"),
            ("India automotive industry OR Indian automaker", "en-US", "US", "US:en"),
            ("Southeast Asia automotive market OR ASEAN automaker", "en-US", "US", "US:en"),
        ],
    },
    "oceania": {
        "label": "オセアニア",
        "flag": "🇦🇺",
        "queries": [
            ("Australia automotive industry OR Australian car market", "en-AU", "AU", "AU:en"),
            ("New Zealand automotive market OR NZ car industry", "en-AU", "AU", "AU:en"),
            ("EV market Australia automaker", "en-AU", "AU", "AU:en"),
        ],
    },
    "africa": {
        "label": "アフリカ",
        "flag": "🌍",
        "queries": [
            ("Africa automotive industry OR African car market", "en-US", "US", "US:en"),
            ("South Africa (automotive industry OR automaker)", "en-US", "US", "US:en"),
            ("(Nigeria OR Egypt OR Morocco) automotive market", "en-US", "US", "US:en"),
        ],
    },
    "middle_east": {
        "label": "中東",
        "flag": "🕌",
        "queries": [
            ("Middle East (automotive industry OR automaker)", "en-US", "US", "US:en"),
            ("UAE automotive market OR Saudi Arabia automotive industry", "en-US", "US", "US:en"),
            ("Gulf automotive market EV", "en-US", "US", "US:en"),
        ],
    },
    "russia": {
        "label": "ロシア",
        "flag": "🇷🇺",
        "queries": [
            ("Russia automotive industry OR Russian automaker", "en-US", "US", "US:en"),
            ("Russia car market sanctions automaker", "en-US", "US", "US:en"),
        ],
    },
}


def _fetch_region(queries: list[tuple], limit_per_query: int = 10) -> dict:
    raw: list[dict] = []
    for query, hl, gl, ceid in queries:
        results = fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query)
        for r in results:
            r["_query_key"] = query
        raw.extend(results)

    deduped = attach_category(dedupe_by_url(raw))
    newest = sort_by_recency(deduped)
    popular = sort_by_relevance(deduped)
    # newestとpopularは同じdictを共有しているため、新着順で処理すれば両方に反映される。
    attach_translations(newest)
    return {"newest": newest, "popular": popular}


def fetch() -> dict:
    return {key: {"label": r["label"], "flag": r["flag"], **_fetch_region(r["queries"])} for key, r in REGIONS.items()}
