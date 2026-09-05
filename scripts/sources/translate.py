"""英語見出しの簡易日本語訳(MyMemory Translation API、APIキー不要)。

無料・無認証の翻訳APIのため、1日あたりの文字数に上限がある(匿名利用で
無料枠5000文字/日程度)。ダッシュボード全体(トヨタ自動車トピックス・自動車産業
トピックス・モータースポーツ・規制動向)の英語見出しが数百件規模になるため、
1回の実行で無料枠を使い切ることがある。

セクションを順番に処理して先着順に枠を使い切ると、後回しになったセクション
(以前は「規制動向」)が毎回ゼロ件になってしまう。これを避けるため、
翻訳は各セクション個別ではなくfetch_data.py側で一括して行い、
全セクションの候補をラウンドロビン(各セクションから1件ずつ)で混ぜてから
順に翻訳する。これにより、枠を使い切って打ち切られた場合でも、
特定のセクションだけが割を食うことがなくなる。連続して一定回数失敗したら
無料枠切れとみなして即座に打ち切り、無駄なリクエストで実行時間を浪費しない。
"""

from __future__ import annotations

import re

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

_JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")

MAX_CONSECUTIVE_FAILURES = 8


def is_english(text: str) -> bool:
    return bool(text) and not _JAPANESE_RE.search(text)


def translate_to_japanese(text: str) -> str | None:
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:480], "langpair": "en|ja"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText")
        if not translated:
            return None
        if "MYMEMORY WARNING" in translated.upper():
            return None
        return translated
    except Exception:  # noqa: BLE001
        return None


def english_candidates(items: list[dict]) -> list[dict]:
    """アイテムのうち英語見出しのものだけを、順序を保って返す。"""
    return [item for item in items if is_english(item.get("title", ""))]


def round_robin(lists: list[list[dict]]) -> list[dict]:
    """複数のリストから1件ずつ順番に取り出して1本のリストに混ぜる。

    特定のリストの件数が多いからといって上位を独占しないようにするための、
    セクション横断での公平な優先順位付け。
    """
    merged: list[dict] = []
    max_len = max((len(lst) for lst in lists), default=0)
    for i in range(max_len):
        for lst in lists:
            if i < len(lst):
                merged.append(lst[i])
    return merged


def translate_batch(candidates: list[dict]) -> None:
    """候補を順に翻訳し、各アイテムのdictへtitle_jaを直接書き込む。

    連続してMAX_CONSECUTIVE_FAILURES回失敗したら、無料枠切れ(または
    エンドポイント不調)とみなして即座に打ち切る。呼び出し側が渡すitemsの
    dictを直接書き換えるため、同じdictを共有する他のソート済みリスト
    (newest/popularなど)にも自動的に反映される。
    """
    consecutive_failures = 0
    for item in candidates:
        ja = translate_to_japanese(item.get("title", ""))
        if ja:
            item["title_ja"] = ja
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                break
