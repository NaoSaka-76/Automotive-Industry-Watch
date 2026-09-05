"""トヨタ自動車に関する最新トピックス(グローバル)。

単一車種ではなくトヨタ自動車という企業全体が対象のため、日本語・英語の
一般的な企業名クエリで広く収集する。レクサス等の関連ブランド単独の記事は
対象外(「トヨタ」を含まない見出しは拾わない)。
"""

from __future__ import annotations

from .categorize import attach_category
from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency, sort_by_relevance

QUERIES = [
    ("トヨタ自動車", "ja", "JP", "JP:ja"),
    ("トヨタ (新型 OR 発表 OR 決算 OR 生産)", "ja", "JP", "JP:ja"),
    ("Toyota Motor Corporation", "en-US", "US", "US:en"),
    ("Toyota (announcement OR earnings OR production OR recall)", "en-US", "US", "US:en"),
    ("Toyota", "en-GB", "GB", "GB:en"),
]


def fetch(limit_per_query: int = 12) -> dict:
    raw: list[dict] = []
    for query, hl, gl, ceid in QUERIES:
        results = fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query)
        for r in results:
            r["_query_key"] = query
        raw.extend(results)

    deduped = attach_category(dedupe_by_url(raw))
    newest = sort_by_recency(deduped)
    popular = sort_by_relevance(deduped)
    return {"newest": newest, "popular": popular}
