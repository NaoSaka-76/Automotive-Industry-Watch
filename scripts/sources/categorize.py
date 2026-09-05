"""自動車産業ニュースの見出しをキーワードベースで自動カテゴライズする。

記事本文は取得できず見出し(と一部ソース名)のみが対象のため、これは厳密な
分類ではなく参考値のヒューリスティックである。UI側にもその旨を明記すること。

カテゴリ: new_product(新製品) / new_tech(新技術) / regulation(規制) /
management(経営) / policy(政策) / other(他)

判定順序が結果を左右する(複数カテゴリのキーワードが同時にヒットする見出しが
多いため)。経験則として、まず政策(政府主体の動き)→規制(基準・認証・リコール)
→経営(企業活動・M&A・決算・人事・生産)→新技術→新製品→他、の優先順で判定する。
"""

from __future__ import annotations

CATEGORY_ORDER = ["policy", "regulation", "management", "new_tech", "new_product", "other"]

CATEGORY_LABELS_JA = {
    "new_product": "新製品",
    "new_tech": "新技術",
    "regulation": "規制",
    "management": "経営",
    "policy": "政策",
    "other": "他",
}

_KEYWORDS: dict[str, list[str]] = {
    "policy": [
        # 日本語
        "補助金", "関税", "政府", "法案", "国会", "規制強化案", "減税", "優遇税制",
        "義務化", "エコカー減税", "禁輸", "輸入規制", "貿易摩擦", "外交",
        # 英語
        "subsidy", "subsidies", "tariff", "tariffs", "government", "policy",
        "bill", "legislation", "trade war", "sanction", "sanctions", "ban on",
        "mandate", "incentive", "tax credit", "administration", "ministry",
        "白宮", "european commission", "eu commission",
    ],
    "regulation": [
        "規制", "排出ガス", "排ガス", "環境基準", "安全基準", "リコール", "認証",
        "型式指定", "車検", "基準strengthen",
        "emission standard", "emissions standard", "emissions rule", "recall",
        "safety standard", "regulator", "regulatory", "type approval",
        "homologation", "compliance", "epa", "nhtsa", "euro 7", "crash test",
    ],
    "management": [
        "決算", "増益", "減益", "赤字", "黒字", "提携", "買収", "合弁", "出資",
        "人事", "社長", "会長", "ceo", "工場", "生産台数", "減産", "増産",
        "株価", "業績", "リストラ", "人員削減", "工場閉鎖", "工場新設", "投資額",
        "merger", "acquisition", "acquire", "joint venture", "partnership",
        "earnings", "profit", "loss", "layoff", "layoffs", "job cuts",
        "ceo", "chairman", "restructuring", "factory", "plant closure",
        "new plant", "production cut", "output cut", "stake", "investment",
        "shares", "stock", "ipo", "quarterly results", "annual results",
    ],
    "new_tech": [
        "新技術", "技術開発", "特許", "全固体電池", "自動運転", "運転支援",
        "水素", "燃料電池", "ソフトウェア定義", "半導体", "電動化技術",
        "solid-state battery", "autonomous driving", "self-driving",
        "adas", "hydrogen", "fuel cell", "software-defined", "semiconductor",
        "battery technology", "ai", "artificial intelligence", "lidar",
        "charging technology", "patent", "r&d", "research and development",
    ],
    "new_product": [
        "新型", "発売", "発表", "デビュー", "新モデル", "フルモデルチェンジ",
        "一部改良", "限定車", "コンセプトカー", "世界初公開", "受注開始",
        "unveil", "unveils", "unveiled", "debut", "reveal", "reveals",
        "revealed", "launch", "launches", "launched", "new model",
        "concept car", "facelift", "world premiere", "on sale", "goes on sale",
    ],
}


def categorize(title: str) -> str:
    if not title:
        return "other"
    lowered = title.lower()
    for category in CATEGORY_ORDER[:-1]:
        for kw in _KEYWORDS[category]:
            if kw.lower() in lowered:
                return category
    return "other"


def attach_category(items: list[dict]) -> list[dict]:
    for item in items:
        item["category"] = categorize(item.get("title", ""))
    return items
