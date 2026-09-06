"""Automotive Industry Watch ダッシュボード用データを収集し、
site/data/latest.json へ出力する。

30分おきにGitHub Actionsから実行される想定。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sources import earnings, industry_news, motorsports, peer_stocks, regulations, stock, toyota_news
from sources.translate import english_candidates, round_robin, translate_batch

JST = timezone(timedelta(hours=9))
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "latest.json"


def build_dashboard() -> dict:
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    sections = {
        "toyota_news": toyota_news.fetch(),
        "toyota_stock": stock.fetch(),
        "toyota_earnings": earnings.fetch(),
        "peer_stocks": peer_stocks.fetch(),
        "industry_news": {"regions": industry_news.fetch()},
        "motorsports": {"categories": motorsports.fetch()},
        "regulations": {"regions": regulations.fetch()},
    }

    _translate_all_sections(sections)

    return {
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_jst": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "sections": sections,
    }


def _translate_all_sections(sections: dict) -> None:
    """英語見出しの日本語訳を、セクションをまたいだラウンドロビンで一括翻訳する。

    セクションごとに個別翻訳すると、無料APIの1日の枠を先着順のセクションが
    使い切ってしまい、後回しのセクションが毎回ゼロ件になる。ここでは
    全セクションの候補(新着順)をラウンドロビンで混ぜてから翻訳することで、
    枠を使い切って途中で打ち切られても、全セクションに公平に翻訳が行き渡る
    ようにする。
    """
    toyota_candidates = english_candidates(sections["toyota_news"]["newest"])

    industry_regions = sections["industry_news"]["regions"]
    industry_candidates = round_robin(
        [english_candidates(r["newest"]) for r in industry_regions.values()]
    )

    ms_categories = sections["motorsports"]["categories"]
    motorsports_candidates = round_robin(
        [english_candidates(c["newest"]) for c in ms_categories.values()]
    )

    reg_regions = sections["regulations"]["regions"]
    reg_lists = []
    for region in reg_regions.values():
        for cat in region["categories"].values():
            reg_lists.append(english_candidates(cat["summary"]["newest"]))
            reg_lists.append(english_candidates(cat["authority"]["newest"]))
    regulations_candidates = round_robin(reg_lists)

    all_candidates = round_robin(
        [toyota_candidates, industry_candidates, motorsports_candidates, regulations_candidates]
    )
    translate_batch(all_candidates)


def _is_error_item(value: object) -> bool:
    return (
        isinstance(value, dict)
        and (
            value.get("source") == "error"
            or str(value.get("title", "")).startswith("[取得エラー]")
        )
    )


def _scrub_error_items(node: object) -> object:
    """一時的な取得失敗で紛れ込んだエラー項目を最終JSONから除去する(UI保険)。"""
    if isinstance(node, dict):
        return {k: _scrub_error_items(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_scrub_error_items(v) for v in node if not _is_error_item(v)]
    return node


def main() -> None:
    dashboard = _scrub_error_items(build_dashboard())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote dashboard data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
