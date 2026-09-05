"""英語見出しの簡易日本語訳(MyMemory Translation API、APIキー不要)。

無料・無認証の翻訳APIのため、1日あたりの文字数に上限がある(匿名利用で
無料枠5000文字/日程度)。上限に達した場合や取得失敗時は翻訳を諦め、
呼び出し側で日本語訳フィールドを省略する(見出し自体は表示されるので
壊れない)。トヨタ自動車トピックスのみを対象とし、1回の実行あたりの
翻訳件数に上限を設けて過度なAPI利用を避ける。
"""

from __future__ import annotations

import re

import requests

from .common import REQUEST_TIMEOUT, USER_AGENT

_JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")

MAX_ITEMS_PER_RUN = 30


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


def attach_translations(items: list[dict], max_items: int = MAX_ITEMS_PER_RUN) -> list[dict]:
    translated_count = 0
    for item in items:
        if translated_count >= max_items:
            break
        title = item.get("title", "")
        if not is_english(title):
            continue
        ja = translate_to_japanese(title)
        translated_count += 1
        if ja:
            item["title_ja"] = ja
    return items
