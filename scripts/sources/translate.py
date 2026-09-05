"""英語見出しの簡易日本語訳(MyMemory Translation API、APIキー不要)。

無料・無認証の翻訳APIのため、1日あたりの文字数に上限がある(匿名利用で
無料枠5000文字/日程度)。ダッシュボード全体(トヨタ自動車トピックス・
自動車産業トピックス・モータースポーツ)の英語見出し全件を対象とするため、
1日の無料枠を超える可能性がある。上限に達した場合や取得失敗時は翻訳を諦め、
呼び出し側で日本語訳フィールドを省略する(見出し自体は表示されるので
壊れない)。新着順で上位のものから翻訳することで、枠を使い切っても
直近の話題は優先的に翻訳される。
"""

from __future__ import annotations

import re

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

_JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")


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


def attach_translations(items: list[dict]) -> list[dict]:
    """英語見出しの全件に翻訳を試みる(新着順など、呼び出し側が渡した順)。

    無料枠を使い切ると個々の呼び出しが失敗するようになるが、
    translate_to_japanese側でNoneを返すだけなので処理は継続する。
    """
    for item in items:
        title = item.get("title", "")
        if not is_english(title):
            continue
        ja = translate_to_japanese(title)
        if ja:
            item["title_ja"] = ja
    return items
