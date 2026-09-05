"""Automotive Industry Watch ダッシュボード用データを収集し、
site/data/latest.json へ出力する。

30分おきにGitHub Actionsから実行される想定。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sources import earnings, industry_news, motorsports, regulations, stock, toyota_news

JST = timezone(timedelta(hours=9))
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "latest.json"


def build_dashboard() -> dict:
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    return {
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_jst": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "sections": {
            "toyota_news": toyota_news.fetch(),
            "toyota_stock": stock.fetch(),
            "toyota_earnings": earnings.fetch(),
            "industry_news": {"regions": industry_news.fetch()},
            "motorsports": {"categories": motorsports.fetch()},
            "regulations": {"regions": regulations.fetch()},
        },
    }


def main() -> None:
    dashboard = build_dashboard()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote dashboard data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
