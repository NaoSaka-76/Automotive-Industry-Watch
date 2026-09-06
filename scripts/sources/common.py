"""Automotive Industry Watch 用の共通ヘルパー。

公式APIキーを使わず、Google News RSS(無料・無認証の公開フィード)のみで
記事情報を収集する。取得元は無料公開エンドポイントのみで、構造変化や
レート制限により結果が空になる場合がある。
"""

from __future__ import annotations

import random
import time
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests

USER_AGENT = (
    "Mozilla/5.0 (compatible; AutomotiveIndustryWatchBot/1.0; "
    "+https://github.com/NaoSaka-76/Automotive-Industry-Watch)"
)

REQUEST_TIMEOUT = 15

# 一時的なサーバー側エラー。Google News RSS は混雑時に 429/503 を返すことがあり、
# 数秒待って再試行すると成功することが多い。
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0  # 秒(指数バックオフの基準)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _get_with_retry(session: requests.Session, url: str) -> requests.Response:
    """一時的なエラー(429/5xx・接続エラー)を指数バックオフで再試行しながら GET する。"""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code in _TRANSIENT_STATUS and attempt < _MAX_RETRIES:
                last_exc = requests.HTTPError(f"{resp.status_code} {resp.reason}", response=resp)
            else:
                resp.raise_for_status()
                return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt >= _MAX_RETRIES:
                raise
        time.sleep(_RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1))
    raise last_exc if last_exc else RuntimeError("request failed")


def fetch_google_news_rss(
    query: str, hl: str = "en-US", gl: str = "US", ceid: str = "US:en", limit: int = 10
) -> list[dict]:
    """Google News RSS検索。APIキー不要の公開フィード。

    フィードの並び順(関連度順)をそのまま `_feed_order` として保持しておく。
    「話題順」タブはこの関連度順を代替指標として用いる(記事本文が取得できず
    実際のエンゲージメント数を測れないため)。
    """
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    items: list[dict] = []
    try:
        resp = _get_with_retry(_session(), url)
        feed = feedparser.parse(resp.content)
        for order, entry in enumerate(feed.entries[:limit]):
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            items.append(
                {
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "source": source or "Google News",
                    "published": entry.get("published", ""),
                    "_feed_order": order,
                }
            )
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Google News RSS 取得失敗（再試行後）: {query!r} -> {exc}")
    return items


def dedupe_by_url(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = item.get("url") or item.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _parse_pubdate(raw: str) -> datetime:
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def sort_by_recency(items: list[dict]) -> list[dict]:
    """"published"(RFC822形式)を新しい順に並べ替える。解析できないものは末尾に回す。"""
    return sorted(items, key=lambda item: _parse_pubdate(item.get("published", "")), reverse=True)


def sort_by_relevance(items: list[dict]) -> list[dict]:
    """Google News検索結果本来の関連度順(_feed_order昇順)に並べ替える。

    クエリを跨いで集約した後は、まずクエリ単位の元順序を保ちつつ、
    複数クエリの結果をラウンドロビンで均等に混ぜる
    (特定クエリの結果だけが上位を占めないようにするため)。
    """
    from collections import defaultdict

    buckets: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []
    for item in items:
        key = item.get("_query_key", "_default")
        if key not in buckets:
            order.append(key)
        buckets[key].append(item)
    for key in buckets:
        buckets[key].sort(key=lambda i: i.get("_feed_order", 0))

    merged: list[dict] = []
    max_len = max((len(v) for v in buckets.values()), default=0)
    for i in range(max_len):
        for key in order:
            bucket = buckets[key]
            if i < len(bucket):
                merged.append(bucket[i])
    return merged


def is_within_24h(item: dict, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    raw = item.get("published", "")
    if not raw:
        return False
    dt = _parse_pubdate(raw)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return False
    return (now - dt).total_seconds() <= 86400
