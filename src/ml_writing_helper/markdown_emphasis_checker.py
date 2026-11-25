"""Check generated documents for unmatched Markdown ** / __ emphasis markers."""

import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Final

from loguru import logger

EMPHASIS_MARKERS: Final[tuple[str, ...]] = ("**", "__")


def find_unclosed_markdown_emphasis(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, marker) pairs for lines with an odd marker count."""
    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for marker in EMPHASIS_MARKERS:
            count = 0
            start = 0
            while True:
                index = line.find(marker, start)
                if index < 0:
                    break
                backslashes = 0
                before = index - 1
                while before >= 0 and line[before] == "\\":
                    backslashes += 1
                    before -= 1
                if backslashes % 2 == 0:
                    count += 1
                start = index + len(marker)
            if count % 2:
                findings.append((line_number, marker))
    return findings


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _html_text(path: Path) -> str:
    parser = _TextExtractor()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parser.parts)


def _pdf_text(path: Path) -> str:
    try:
        import fitz
    except ImportError:
        logger.warning(f"[check-miss-bracket] PDF 検査には PyMuPDF が必要です: {path}")
        return ""
    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return "\n".join(
            re.sub(r"<[^>]+>", "", archive.read(name).decode("utf-8", errors="replace"))
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        )


def _epub_text(path: Path) -> str:
    parser_parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.lower().endswith((".html", ".xhtml", ".htm")):
                parser = _TextExtractor()
                parser.feed(archive.read(name).decode("utf-8", errors="replace"))
                parser_parts.extend(parser.parts)
    return "\n".join(parser_parts)


def extract_output_text(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix == ".html" or suffix == ".htm":
            return _html_text(path)
        if suffix == ".pdf":
            return _pdf_text(path)
        if suffix == ".docx":
            return _docx_text(path)
        if suffix == ".epub":
            return _epub_text(path)
    except (OSError, zipfile.BadZipFile) as e:
        logger.warning(f"[check-miss-bracket] 出力を読み込めませんでした: {path} ({e})")
    return ""


def check_markdown_emphasis(path: Path) -> list[tuple[int, str]]:
    """Inspect a generated HTML/PDF/DOCX/EPUB file and return unclosed marker locations."""
    text = extract_output_text(path)
    if not text:
        return []
    return find_unclosed_markdown_emphasis(text)


def check_output_markdown_emphasis(path: Path) -> None:
    """Log warnings for unmatched Markdown emphasis markers in a generated file."""
    for line_number, marker in check_markdown_emphasis(path):
        logger.warning(
            f"[check-miss-bracket] {path}: {line_number}行目に {marker} の閉じ忘れがあります"
        )
