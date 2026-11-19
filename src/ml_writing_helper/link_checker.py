"""--check-link: .md / .html 内の http(s) リンク先を確認し、最終ステータスが 200 以外なら警告する（終了コードは変えない）"""

import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Final

from loguru import logger

LINK_CHECK_SUFFIXES: Final[frozenset[str]] = frozenset({".md", ".html"})
_URL_RE: Final = re.compile(r"https?://[^\s<>\"'`)\]]+")
_TRAILING_PUNCTUATION: Final[str] = ".,;:!?。、"
_TIMEOUT_SEC: Final[float] = 10
_MAX_WORKERS: Final[int] = 8
_HEADERS: Final[dict[str, str]] = {"User-Agent": "Mozilla/5.0 (ml_writing_helper check-link)"}


def extract_links(text: str) -> list[str]:
    """本文中の http(s) リンクを出現順・重複なしで返す。"""
    urls = (m.rstrip(_TRAILING_PUNCTUATION) for m in _URL_RE.findall(text))
    return list(dict.fromkeys(u for u in urls if u))


def check_status(url: str) -> int | str:
    """リダイレクトを辿った最終の HTTP ステータスを返す。取得できなければ失敗理由の文字列を返す。"""
    request = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SEC) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError, ValueError) as e:
        return str(getattr(e, "reason", e))


def check_links(path: Path) -> None:
    """path が .md / .html なら、その中のリンク先を確認して 200 以外を警告する。"""
    if path.suffix.lower() not in LINK_CHECK_SUFFIXES:
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.warning(f"[check-link] 読み込めませんでした: {path} ({e})")
        return
    urls = extract_links(text)
    if not urls:
        return
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        statuses = list(pool.map(check_status, urls))
    for url, status in zip(urls, statuses):
        if status != 200:
            logger.warning(f"[check-link] {path}: {url} → {status}")
