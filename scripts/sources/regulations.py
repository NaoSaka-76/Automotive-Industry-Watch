"""自動車開発に影響を与える規制動向(日本・アメリカ・ヨーロッパ・中国)。

対象カテゴリー: 排気規制 / 安全性能規制 / 騒音規制 / サイバーセキュリティ規制。
各地域×カテゴリーごとに2種類のニュースを集約する:
  - summary: 規制動向そのものに関する一般ニュース(業界の反応・解説記事等を含む)
  - authority: 規制を所管する当局(国土交通省・NHTSA・欧州委員会/UNECE・MIIT等)の
    名称を含む、当局発の動き寄りのニュース

日本以外は英語で報じられた国際ニュースを対象とする(他セクションと同じ設計方針)。
"""

from __future__ import annotations

from .common import dedupe_by_url, fetch_google_news_rss, sort_by_recency, sort_by_relevance

CATEGORY_ORDER = ["emissions", "safety", "noise", "cybersecurity"]
CATEGORY_LABELS = {
    "emissions": "排気規制",
    "safety": "安全性能規制",
    "noise": "騒音規制",
    "cybersecurity": "サイバーセキュリティ規制",
}

REGIONS: dict[str, dict] = {
    "japan": {
        "label": "日本",
        "flag": "🇯🇵",
        "categories": {
            "emissions": {
                "summary": [("自動車 (排出ガス規制 OR 排ガス規制 OR 燃費基準 OR CO2規制)", "ja", "JP", "JP:ja")],
                "authority": [("(国土交通省 OR 環境省) (排出ガス OR 排ガス規制 OR 燃費基準)", "ja", "JP", "JP:ja")],
            },
            "safety": {
                "summary": [("自動車 (安全基準 OR 保安基準 OR 衝突安全 OR 自動運転 規制)", "ja", "JP", "JP:ja")],
                "authority": [("国土交通省 (保安基準 OR 型式指定 OR 安全基準)", "ja", "JP", "JP:ja")],
            },
            "noise": {
                "summary": [("自動車 (騒音規制 OR 騒音基準)", "ja", "JP", "JP:ja")],
                "authority": [("(国土交通省 OR 環境省) 自動車 騒音規制", "ja", "JP", "JP:ja")],
            },
            "cybersecurity": {
                "summary": [("自動車 (サイバーセキュリティ規制 OR サイバーセキュリティ基準 OR ソフトウェア更新規制)", "ja", "JP", "JP:ja")],
                "authority": [("国土交通省 (サイバーセキュリティ OR UN-R155 OR 不正アクセス対策)", "ja", "JP", "JP:ja")],
            },
        },
    },
    "us": {
        "label": "アメリカ",
        "flag": "🇺🇸",
        "categories": {
            "emissions": {
                "summary": [
                    ("vehicle OR automotive OR car emissions (regulation OR standard OR rule)", "en-US", "US", "US:en"),
                    ("CARB California emissions standard vehicle", "en-US", "US", "US:en"),
                ],
                "authority": [
                    ("EPA (vehicle OR auto OR car) emissions (rule OR standard OR regulation)", "en-US", "US", "US:en"),
                    ("CARB (rule OR regulation OR waiver) vehicle emissions", "en-US", "US", "US:en"),
                ],
            },
            "safety": {
                "summary": [("vehicle safety (regulation OR standard OR rule) FMVSS", "en-US", "US", "US:en")],
                "authority": [("NHTSA (safety standard OR rule OR regulation)", "en-US", "US", "US:en")],
            },
            "noise": {
                "summary": [("vehicle noise (regulation OR standard)", "en-US", "US", "US:en")],
                "authority": [("NHTSA OR EPA vehicle noise (regulation OR standard)", "en-US", "US", "US:en")],
            },
            "cybersecurity": {
                "summary": [("vehicle cybersecurity (regulation OR standard)", "en-US", "US", "US:en")],
                "authority": [("NHTSA vehicle cybersecurity (guidance OR rule OR regulation)", "en-US", "US", "US:en")],
            },
        },
    },
    "europe": {
        "label": "ヨーロッパ",
        "flag": "🇪🇺",
        "categories": {
            "emissions": {
                "summary": [("EU (vehicle OR car) emissions (regulation OR standard) \"Euro 7\"", "en-GB", "GB", "GB:en")],
                "authority": [("\"European Commission\" OR UNECE vehicle emissions regulation", "en-GB", "GB", "GB:en")],
            },
            "safety": {
                "summary": [("EU vehicle safety regulation \"General Safety Regulation\"", "en-GB", "GB", "GB:en")],
                "authority": [("UNECE OR \"European Commission\" vehicle safety regulation", "en-GB", "GB", "GB:en")],
            },
            "noise": {
                "summary": [("EU vehicle noise (regulation OR standard)", "en-GB", "GB", "GB:en")],
                "authority": [("UNECE OR \"European Commission\" vehicle noise regulation", "en-GB", "GB", "GB:en")],
            },
            "cybersecurity": {
                "summary": [("EU vehicle cybersecurity regulation UNECE", "en-GB", "GB", "GB:en")],
                "authority": [("UNECE (R155 OR R156 OR cybersecurity regulation)", "en-GB", "GB", "GB:en")],
            },
        },
    },
    "china": {
        "label": "中国",
        "flag": "🇨🇳",
        "categories": {
            "emissions": {
                "summary": [("China vehicle emissions standard \"China 6\"", "en-US", "US", "US:en")],
                "authority": [("MIIT OR \"Ministry of Ecology and Environment\" China vehicle emissions", "en-US", "US", "US:en")],
            },
            "safety": {
                "summary": [("China vehicle safety standard regulation", "en-US", "US", "US:en")],
                "authority": [("MIIT China vehicle safety (standard OR regulation)", "en-US", "US", "US:en")],
            },
            "noise": {
                "summary": [("China vehicle noise standard regulation", "en-US", "US", "US:en")],
                "authority": [("MIIT China vehicle noise standard", "en-US", "US", "US:en")],
            },
            "cybersecurity": {
                "summary": [("China automotive data security cybersecurity regulation", "en-US", "US", "US:en")],
                "authority": [("CAC OR MIIT China automotive data security regulation", "en-US", "US", "US:en")],
            },
        },
    },
}


def _fetch_group(queries: list[tuple], limit_per_query: int = 10) -> dict:
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
    result: dict = {}
    for region_key, region in REGIONS.items():
        categories = {}
        for cat_key in CATEGORY_ORDER:
            cat_cfg = region["categories"][cat_key]
            categories[cat_key] = {
                "label": CATEGORY_LABELS[cat_key],
                "summary": _fetch_group(cat_cfg["summary"]),
                "authority": _fetch_group(cat_cfg["authority"]),
            }
        result[region_key] = {"label": region["label"], "flag": region["flag"], "categories": categories}
    return result
