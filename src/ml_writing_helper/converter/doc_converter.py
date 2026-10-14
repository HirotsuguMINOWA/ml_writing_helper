"""
Markdown/HTML を PDF/HTML/DOCX へ変換する処理（md2pdf.py から移植）

- .md は中身を見て marp / slidev / pandoc / playwright を使い分ける
  - mermaid / plantuml ブロックを含む .md を PDF にする場合は playwright（headless Chromium）で描画する
- .html 入力は Chrome/Chromium の headless print で PDF、pandoc で DOCX にする
- 出力先は src ルートからの相対フォルダ構成を dst ルートに再現する

外部ツール（無いものはその変換だけ使えない）:
    pandoc(+lualatex), plantuml, marp (または npx), slidev (または npx), Chrome/Chromium,
    playwright (pip install playwright && playwright install chromium)
"""
import json
import platform
import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Final

from loguru import logger

DOC_OUTPUT_FORMATS: Final[tuple[str, ...]] = ("pdf", "html", "docx")
DOC_ENGINES: Final[tuple[str, ...]] = ("auto", "pandoc", "playwright", "marp", "slidev")
DEFAULT_DOC_OUTPUT_FORMATS: Final[tuple[str, ...]] = ("pdf",)
DEFAULT_DOC_ENGINE: Final[str] = "auto"
DEFAULT_INPUT_PATTERNS: Final[tuple[str, ...]] = ("*.md",)
SUPPORTED_INPUT_SUFFIXES: Final[tuple[str, ...]] = (".md", ".html")

# lualatex で日本語を通すための既定ヘッダー（--header 未指定時に使う）
DEFAULT_HEADER_TEX_TEXT: Final[str] = "\\usepackage{luatexja}\n\\usepackage{luatexja-fontspec}\n"

PANDOC_TEXT_REPLACEMENTS: Final[dict[int, str]] = {
    ord("\uFE0F"): "",  # Variation Selector-16: emoji presentation
    ord("✅"): "[OK]",
    ord("❌"): "[NG]",
    ord("⭕"): "[OK]",
    ord("⚠"): "[WARN]",
    ord("☕"): "[BREAK]",
    ord("🎉"): "[CELEBRATE]",
    ord("📝"): "[NOTE]",
    ord("💡"): "[IDEA]",
    ord("🚀"): "[START]",
    ord("📌"): "[PIN]",
    ord("🔧"): "[FIX]",
    ord("🎯"): "[GOAL]",
    ord("📁"): "[FILE]",
    ord("🌟"): "[STAR]",
    ord("▶"): "[PLAY]",
    ord("🔴"): "[RED]",
    ord("🟢"): "[GREEN]",
}

MERMAID_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
PLANTUML_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"```plantuml\n(.*?)```", re.DOTALL)

DEFAULT_CHROME_CANDIDATES: Final[tuple[Path, ...]] = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
)


def has_diagram_blocks(text: str) -> bool:
    return bool(MERMAID_BLOCK_RE.search(text) or PLANTUML_BLOCK_RE.search(text))


def sanitize_markdown_for_pandoc(markdown_text: str) -> tuple[str, bool]:
    """Replace Unicode sequences that are known to crash LuaLaTeX emoji shaping."""
    sanitized = markdown_text.translate(PANDOC_TEXT_REPLACEMENTS)
    return sanitized, sanitized != markdown_text


def normalize_input_patterns(input_patterns: Sequence[str | re.Pattern[str]] | None) -> list[re.Pattern[str]]:
    """変換対象ファイル名のパターンをコンパイルする。ファイル名（base name）全体に fullmatch する。

    glob 的な `*` は `.*`（任意文字 0 文字以上）に、ドットはリテラルの点に展開する。
        "*.md"      -> ".*\\.md"       (すべての .md ファイル)
        "*_marp.md" -> ".*_marp\\.md"  (_marp.md で終わるファイル)
    Raises ValueError.
    """
    resolved: list[re.Pattern[str]] = []
    seen: set[str] = set()
    for pattern in input_patterns or DEFAULT_INPUT_PATTERNS:
        if isinstance(pattern, re.Pattern):
            compiled = pattern
        else:
            expr = (pattern or "").strip()
            if not expr:
                continue
            expr = "".join(".*" if ch == "*" else "\\." if ch == "." else ch for ch in expr)
            try:
                compiled = re.compile(expr)
            except re.error as e:
                raise ValueError(f"Invalid input pattern: {pattern!r} ({e})") from e
        if compiled.pattern not in seen:
            seen.add(compiled.pattern)
            resolved.append(compiled)
    if not resolved:
        raise ValueError("At least one input pattern must be specified")
    return resolved


def _log_error(message: str, exc: Exception) -> None:
    logger.error(f"{message}: {exc}")
    logger.opt(exception=exc).debug(message)


# -------------------------------------------------------
# ツール存在確認（必要になったときに1回だけ確認する）
# -------------------------------------------------------
@cache
def _pandoc_bin() -> str | None:
    found = shutil.which("pandoc")
    if found is None:
        logger.warning("pandoc not found. Install: brew install pandoc / sudo apt-get install pandoc")
    return found


@cache
def _marp_cmd() -> tuple[str, ...] | None:
    found = shutil.which("marp")
    if found:
        return (found,)
    if shutil.which("npx"):
        return ("npx", "--yes", "@marp-team/marp-cli")
    logger.warning("marp-cli not found. Install: npm install -g @marp-team/marp-cli")
    return None


@cache
def _slidev_cmd() -> tuple[str, ...] | None:
    found = shutil.which("slidev")
    if found:
        return (found,)
    if shutil.which("npx"):
        return ("npx", "@slidev/cli")
    logger.warning("slidev not found. Install: npm install -g @slidev/cli")
    return None


@cache
def _plantuml_available() -> bool:
    if shutil.which("plantuml"):
        return True
    logger.warning("plantuml CLI not found. PlantUML blocks will not be converted to diagrams.")
    return False


@cache
def _chrome_binary() -> str | None:
    for candidate in DEFAULT_CHROME_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    logger.warning("Chrome/Chromium not found. HTML to PDF conversion is unavailable.")
    return None


@cache
def playwright_available() -> bool:
    """playwright と headless Chromium を確認する。Chromium が無ければ自動インストールを試みる。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning(
            "playwright not installed. mermaid/plantuml diagrams in PDF are unavailable.\n"
            "  Fix: pip install playwright && playwright install chromium"
        )
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch(timeout=10000).close()
        return True
    except Exception:
        logger.info("Playwright chromium not found. Running `playwright install chromium`...")
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"Failed to install Playwright chromium:\n{result.stderr}\n  Fix: playwright install chromium")
        return False
    logger.info("Playwright chromium installed successfully.")
    return True


@cache
def _default_header_tex() -> str:
    path = Path(tempfile.gettempdir()) / "ml_writing_helper_doc_conv_header.tex"
    path.write_text(DEFAULT_HEADER_TEX_TEXT, encoding="utf-8")
    return str(path)


def _pandoc_pdf_args() -> list[str]:
    args = ["-t", "pdf", "--pdf-engine=lualatex"]
    if platform.system() == "Darwin":
        for key in ("mainfont", "sansfont", "monofont"):
            args.extend(["-V", f"{key}=Hiragino Kaku Gothic ProN"])
    return args


def _run(cmd: Sequence[str], cwd: Path, label: str, stdin: str | None = None, timeout: float | None = None) -> bool:
    logger.debug(f"Running {label}: {list(cmd)} (cwd={cwd})")
    result = subprocess.run(
        list(cmd), input=stdin, capture_output=True, text=True, encoding="utf-8", cwd=str(cwd), timeout=timeout
    )
    if result.stdout:
        logger.debug(result.stdout)
    if result.returncode != 0:
        logger.error(f"{label} failed (exit {result.returncode}):\n{result.stderr}")
        return False
    if result.stderr:
        logger.debug(result.stderr)
    return True


class DocConverter:
    """Markdown/HTML ファイルを指定形式（複数可）へ変換する。"""

    def __init__(
            self,
            src_root: str | Path,
            dst_root: str | Path,
            output_formats: Sequence[str] = DEFAULT_DOC_OUTPUT_FORMATS,
            engine: str = DEFAULT_DOC_ENGINE,
            input_patterns: Sequence[str | re.Pattern[str]] | None = None,
            header_files: Sequence[str | Path] = (),
            marp_header_files: Sequence[str | Path] = (),
    ) -> None:
        self.src_root: Final[Path] = Path(src_root)
        self.dst_root: Final[Path] = Path(dst_root)
        self.output_formats: Final[tuple[str, ...]] = tuple(dict.fromkeys(f.lower() for f in output_formats))
        for fmt in self.output_formats:
            if fmt not in DOC_OUTPUT_FORMATS:
                raise ValueError(f"Unsupported output format: {fmt}. Supported: {', '.join(DOC_OUTPUT_FORMATS)}")
        if engine not in DOC_ENGINES:
            raise ValueError(f"Unsupported engine: {engine}. Supported: {', '.join(DOC_ENGINES)}")
        self.engine: Final[str] = engine
        self.input_patterns: Final[list[re.Pattern[str]]] = normalize_input_patterns(input_patterns)
        self.header_files: Final[tuple[str, ...]] = tuple(str(h) for h in header_files)
        self.marp_header_files: Final[tuple[Path, ...]] = tuple(Path(h) for h in marp_header_files)

    # -------------------------------------------------------
    # 対象判定・出力パス
    # -------------------------------------------------------
    def is_input_file(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES and any(
            pat.fullmatch(path.name) for pat in self.input_patterns
        )

    def dst_path(self, src_file: Path, fmt: str | None = None) -> Path:
        """src_root からの相対位置を dst_root に再現したパス。fmt を与えると拡張子を置き換える。"""
        try:
            relative = src_file.resolve().relative_to(self.src_root.resolve())
        except ValueError:
            relative = Path(src_file.name)
        if fmt is not None:
            relative = relative.with_suffix(f".{fmt}")
        return self.dst_root / relative

    def dst_paths(self, src_file: Path) -> list[Path]:
        return [self.dst_path(src_file, fmt) for fmt in self.output_formats]

    # -------------------------------------------------------
    # ファイル種別判定
    # -------------------------------------------------------
    @staticmethod
    def _read_head(md_file: Path, max_lines: int = 50) -> str:
        try:
            with open(md_file, encoding="utf-8") as f:
                return "".join(line for _, line in zip(range(max_lines), f))
        except Exception as e:
            _log_error(f"Error reading file {md_file}", e)
            return ""

    @classmethod
    def is_marp_file(cls, md_file: Path) -> bool:
        head = cls._read_head(md_file)
        return any(kw in head for kw in ("marp: true", "marp:true"))

    @classmethod
    def is_slidev_file(cls, md_file: Path) -> bool:
        head = cls._read_head(md_file)
        has_keyword = any(kw in head for kw in ("slidev:", "theme:", "layout:"))
        return head.startswith("---") and has_keyword and not cls.is_marp_file(md_file)

    # -------------------------------------------------------
    # 変換の入口
    # -------------------------------------------------------
    def convert(self, src_file: Path) -> bool:
        """src_file を全ての出力形式へ変換する。1つでも失敗すれば False。"""
        all_ok = True
        for fmt in self.output_formats:
            output_file = self.dst_path(src_file, fmt)
            if output_file.resolve() == src_file.resolve():
                logger.debug(f"Skip: output is the source itself: {src_file}")
                continue
            output_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                ok = self._convert_one(src_file, output_file, fmt)
            except Exception as e:
                _log_error(f"Conversion failed: {src_file} -> {output_file}", e)
                ok = False
            all_ok = all_ok and ok
        return all_ok

    def _convert_one(self, src_file: Path, output_file: Path, fmt: str) -> bool:
        suffix = src_file.suffix.lower()
        if suffix == ".html":
            if fmt == "html":
                shutil.copy2(src_file, output_file)
                logger.info(f"[html-copy] {src_file} -> {output_file}")
                return True
            if fmt == "docx":
                return self.convert_html_to_docx(src_file, output_file)
            return self.convert_html_to_pdf(src_file, output_file)

        if suffix != ".md":
            logger.error(f"Unsupported source file: {src_file}")
            return False

        engine = self.engine
        if engine == "auto":
            engine = self._auto_engine(src_file, fmt)
        elif (engine == "marp" and fmt == "docx") or (engine == "slidev" and fmt != "pdf"):
            logger.warning(f"{engine} engine does not support {fmt}; falling back to pandoc")
            engine = "pandoc"
        elif engine == "playwright" and fmt == "docx":
            engine = "pandoc"

        if engine == "marp":
            return self.convert_with_marp(src_file, output_file, fmt)
        if engine == "slidev":
            return self.convert_with_slidev(src_file, output_file)
        if engine == "playwright":
            if fmt == "html":
                return self.convert_to_html(src_file, output_file)
            return self.convert_with_playwright(src_file, output_file)
        return self.convert_with_pandoc(src_file, output_file, fmt)

    def _auto_engine(self, md_file: Path, fmt: str) -> str:
        if fmt in ("pdf", "html") and self.is_marp_file(md_file) and _marp_cmd():
            return "marp"
        if fmt == "pdf" and self.is_slidev_file(md_file) and _slidev_cmd():
            return "slidev"
        if fmt == "html":
            # mermaid.js / highlight.js / KaTeX 入りのブラウザ向け HTML
            return "playwright"
        if fmt == "pdf" and has_diagram_blocks(md_file.read_text(encoding="utf-8")) and playwright_available():
            return "playwright"
        return "pandoc"

    # -------------------------------------------------------
    # pandoc
    # -------------------------------------------------------
    def convert_with_pandoc(self, md_file: Path, output_file: Path, fmt: str) -> bool:
        """pandoc で指定形式に変換する。PDF は emoji を含んでも落ちにくくする。"""
        pandoc = _pandoc_bin()
        if pandoc is None:
            logger.error(f"pandoc is required to convert: {md_file}")
            return False
        markdown_text = md_file.read_text(encoding="utf-8")
        cmd = [pandoc, "-", "--resource-path", str(md_file.parent)]

        if fmt == "pdf":
            markdown_text, was_sanitized = sanitize_markdown_for_pandoc(markdown_text)
            if was_sanitized:
                logger.warning(f"Replaced problematic Unicode emoji sequences before pandoc conversion: {md_file}")
            cmd.extend(_pandoc_pdf_args())
            cmd.append("--no-highlight")
            for header_file in self.header_files or (_default_header_tex(),):
                cmd.extend(["-H", header_file])
        elif fmt == "html":
            if _plantuml_available():
                markdown_text = self._replace_plantuml_with_svg(markdown_text)
            cmd.extend(["-t", "html5", "--standalone", "--metadata", f"pagetitle={md_file.stem}"])

        cmd.extend(["-o", str(output_file)])
        if not _run(cmd, cwd=md_file.parent, label="pandoc", stdin=markdown_text):
            return False
        logger.info(f"[pandoc] {md_file} -> {output_file}")
        return True

    # -------------------------------------------------------
    # playwright（mermaid / plantuml / KaTeX をブラウザで描画）
    # -------------------------------------------------------
    @staticmethod
    def _replace_plantuml_with_svg(md_text: str) -> str:
        """plantuml コードブロックを inline SVG に置換する"""

        def replace(m: re.Match[str]) -> str:
            with tempfile.TemporaryDirectory(prefix="ml_writing_helper-puml-") as tmp:
                puml_path = Path(tmp) / "diagram.puml"
                puml_path.write_text("@startuml\n" + m.group(1) + "\n@enduml", encoding="utf-8")
                try:
                    subprocess.run(["plantuml", "-tsvg", str(puml_path)], capture_output=True, check=True)
                    svg = puml_path.with_suffix(".svg").read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"PlantUML conversion failed: {e}")
                    return m.group(0)
            svg = re.sub(r"<\?xml[^>]+\?>", "", svg).strip()
            return f'\n\n<div class="plantuml-diagram">{svg}</div>\n\n'

        return PLANTUML_BLOCK_RE.sub(replace, md_text)

    def build_browser_html(self, md_text: str) -> str:
        """marked.js + mermaid.js + highlight.js + KaTeX を埋め込んだ HTML 文字列を生成する"""
        if PLANTUML_BLOCK_RE.search(md_text) and _plantuml_available():
            md_text = self._replace_plantuml_with_svg(md_text)
        md_json = json.dumps(md_text).replace("</", "<\\/")
        return _BROWSER_HTML_TEMPLATE.replace("__MD_JSON__", md_json)

    def convert_to_html(self, md_file: Path, output_file: Path) -> bool:
        """MD → ブラウザ向け HTML（mermaid.js 等は CDN から読み込む）"""
        html = self.build_browser_html(md_file.read_text(encoding="utf-8"))
        output_file.write_text(html, encoding="utf-8")
        logger.info(f"[html-template] {md_file} -> {output_file}")
        return True

    def convert_with_playwright(self, md_file: Path, output_file: Path) -> bool:
        """Playwright で MD（mermaid/plantuml 含む）→ PDF 変換"""
        if not playwright_available():
            logger.warning(f"playwright unavailable; falling back to pandoc: {md_file}")
            return self.convert_with_pandoc(md_file, output_file, "pdf")
        from playwright.sync_api import sync_playwright

        html = self.build_browser_html(md_file.read_text(encoding="utf-8"))
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                # set_content() を使うことで file:// 制約なしに CDN スクリプトを読み込める
                page.set_content(html, wait_until="domcontentloaded")
                page.wait_for_selector('[data-ready="true"]', timeout=60000)
                page.pdf(path=str(output_file), print_background=True, format="A4")
            finally:
                browser.close()
        logger.info(f"[playwright] {md_file} -> {output_file}")
        return True

    # -------------------------------------------------------
    # marp / slidev
    # -------------------------------------------------------
    @staticmethod
    def _normalize_marp_header_fragment(text: str) -> str:
        """Marp に挿入する frontmatter 断片から --- を取り除く。"""
        stripped = text.lstrip("\ufeff").strip()
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[0].strip() == "---":
            for idx in range(1, len(lines)):
                if lines[idx].strip() in ("---", "..."):
                    return "\n".join(lines[1:idx]).strip()
        return stripped

    def _load_marp_header_text(self) -> str:
        fragments: list[str] = []
        for header_path in self.marp_header_files:
            try:
                fragment = self._normalize_marp_header_fragment(header_path.read_text(encoding="utf-8"))
            except Exception as e:
                _log_error(f"Error reading marp header file {header_path}", e)
                continue
            if fragment:
                fragments.append(fragment)
        return "\n".join(fragments).strip()

    @staticmethod
    def _inject_marp_header(markdown_text: str, header_text: str) -> str:
        lines = markdown_text.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            return "".join([lines[0], f"{header_text.rstrip()}\n", *lines[1:]])
        return f"---\n{header_text.rstrip()}\n---\n\n{markdown_text.lstrip(chr(0xFEFF))}"

    def convert_with_marp(self, md_file: Path, output_file: Path, fmt: str) -> bool:
        marp = _marp_cmd()
        if marp is None:
            logger.warning(f"marp unavailable; falling back to pandoc: {md_file}")
            return self.convert_with_pandoc(md_file, output_file, fmt)
        header_text = self._load_marp_header_text()
        temp_md: Path | None = None
        marp_input = md_file
        try:
            if header_text:
                # 相対パスの画像を解決できるよう、元ファイルと同じフォルダに一時ファイルを作る
                with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", suffix=".md", prefix=f".{md_file.stem}.marp.",
                        dir=str(md_file.parent), delete=False,
                ) as f:
                    f.write(self._inject_marp_header(md_file.read_text(encoding="utf-8"), header_text))
                    temp_md = marp_input = Path(f.name)
            cmd = [*marp, *(["--pdf"] if fmt == "pdf" else []), "--allow-local-files",
                   marp_input.name, "-o", str(output_file.resolve())]
            if not _run(cmd, cwd=md_file.parent, label="marp"):
                return False
        finally:
            if temp_md is not None:
                temp_md.unlink(missing_ok=True)
        logger.info(f"[marp] {md_file} -> {output_file}")
        return True

    def convert_with_slidev(self, md_file: Path, output_file: Path) -> bool:
        slidev = _slidev_cmd()
        if slidev is None:
            logger.warning(f"slidev unavailable; falling back to pandoc: {md_file}")
            return self.convert_with_pandoc(md_file, output_file, "pdf")
        cmd = [*slidev, "export", md_file.name, "--format", "pdf", "--output", str(output_file.resolve())]
        if not _run(cmd, cwd=md_file.parent, label="slidev"):
            return False
        logger.info(f"[slidev] {md_file} -> {output_file}")
        return True

    # -------------------------------------------------------
    # HTML 入力
    # -------------------------------------------------------
    @staticmethod
    def convert_html_to_docx(html_file: Path, output_file: Path) -> bool:
        pandoc = _pandoc_bin()
        if pandoc is None:
            return False
        cmd = [pandoc, str(html_file), "--resource-path", str(html_file.parent), "-o", str(output_file)]
        if not _run(cmd, cwd=html_file.parent, label="pandoc (html -> docx)"):
            return False
        logger.info(f"[html-docx] {html_file} -> {output_file}")
        return True

    @staticmethod
    def convert_html_to_pdf(html_file: Path, output_file: Path) -> bool:
        chrome = _chrome_binary()
        if chrome is None:
            logger.error(f"HTML to PDF requires Chrome or Chromium: {html_file}")
            return False
        with tempfile.TemporaryDirectory(prefix="ml_writing_helper-chrome-") as user_data_dir:
            cmd = [
                chrome, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                f"--user-data-dir={user_data_dir}", "--allow-file-access-from-files",
                "--print-to-pdf-no-header", f"--print-to-pdf={output_file.resolve()}",
                html_file.resolve().as_uri(),
            ]
            if not _run(cmd, cwd=html_file.parent, label="chrome (html -> pdf)", timeout=50):
                return False
        logger.info(f"[html-pdf] {html_file} -> {output_file}")
        return True


_BROWSER_HTML_TEMPLATE: Final[str] = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<style>
  body { font-family: "Hiragino Kaku Gothic ProN", sans-serif;
         max-width: 900px; margin: 0 auto; padding: 2em; }
  pre { background: #f6f8fa; border-radius: 6px; padding: 1em; overflow-x: auto; }
  pre code.hljs { background: transparent; padding: 0; }
  .mermaid { text-align: center; }
  table { border-collapse: collapse; border: 1px solid #000; }
  th, td { border: 1px solid #000; padding: 0.5em; }
  table caption { font-weight: bold; margin: 1em 0; }
</style>
</head>
<body>
<div id="content"></div>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/highlight.min.js"></script>
<script>
  // mermaid コードブロックを <div class="mermaid"> に変換するカスタムレンダラー
  marked.use({
    gfm: true,
    renderer: {
      code({ text, lang }) {
        if (lang === 'mermaid') {
          return '<div class="mermaid">' + text + '</div>';
        }
        return false;
      }
    }
  });

  const md = __MD_JSON__;
  const content = document.getElementById('content');

  // コードブロック内の $ を KaTeX に誤認識されないよう、一時的にプレースホルダに置き換えて marked.parse する。
  var U2500 = String.fromCharCode(0x2500);
  var PH_START = U2500 + 'CODEBLOCKSTART' + U2500;
  var PH_END = U2500 + 'CODEBLOCKEND' + U2500;
  var savedBlocks = [];
  var mdForParse = md.replace(/```([\s\S]*?)```/g, function(m) {
    savedBlocks.push(m);
    return PH_START + (savedBlocks.length - 1) + PH_END;
  });

  content.innerHTML = marked.parse(mdForParse);

  var BS = '\\';
  var codeRe = new RegExp(PH_START + '(' + BS + 'd+)' + PH_END, 'g');
  content.innerHTML = content.innerHTML.replace(codeRe, function(_, idx) {
    return marked.parse(savedBlocks[parseInt(idx, 10)]);
  });

  try {
    document.querySelectorAll('pre code').forEach(function(el) { hljs.highlightElement(el); });
  } catch(e) {
    console.error('hljs highlighting error:', e);
  }

  try {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(content, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: BS + '[', right: BS + ']', display: true },
          { left: BS + '(', right: BS + ')', display: false }
        ],
        throwOnError: false
      });
    }
  } catch(e) {
    console.error('KaTeX rendering error:', e);
  }

  // スクリプト読み込みエラーや mermaid 描画エラー時でも必ず data-ready をセット
  function markReady() {
    requestAnimationFrame(function() { document.body.setAttribute('data-ready', 'true'); });
  }
  var _fallbackTimer = setTimeout(markReady, 25000);
  try {
    mermaid.initialize({ startOnLoad: false });
    mermaid.run({ querySelector: '.mermaid' }).then(function() {
      clearTimeout(_fallbackTimer);
      markReady();
    }).catch(function(e) {
      console.error('mermaid rendering error:', e);
      clearTimeout(_fallbackTimer);
      markReady();
    });
  } catch(e) {
    console.error('mermaid init error:', e);
    clearTimeout(_fallbackTimer);
    markReady();
  }
</script>
</body>
</html>"""
