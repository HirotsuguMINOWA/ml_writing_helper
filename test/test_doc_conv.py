from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from ml_writing_helper.config import ConfigError, DocConvTaskConfig, parse_config
from ml_writing_helper.converter.doc_converter import DocConverter, normalize_input_patterns
from ml_writing_helper.main import _parse_cli_args, _watch_config_from_cli
from ml_writing_helper.task_runner.doc_conv_runner import DocConvTask

needs_pandoc = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is not installed")


def test_normalize_input_patterns_glob() -> None:
    pats = normalize_input_patterns(["*_marp.md"])
    assert pats[0].fullmatch("a_marp.md")
    assert not pats[0].fullmatch("a.md")


def test_parse_config_doc_conv_defaults(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    config = parse_config({"mode": "doc_conv", "src": "docs"}, base_dir=tmp_path)
    task = config.tasks[0]
    assert isinstance(task, DocConvTaskConfig)
    assert task.dst == task.src == (tmp_path / "docs").resolve()
    assert task.formats == ("pdf",)
    assert task.engine == "auto"
    assert task.patterns == ("*.md",)


def test_parse_config_doc_conv_errors(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    with pytest.raises(ConfigError) as e:
        _ = parse_config(
            {"mode": "doc_conv", "src": "docs", "ext": ["pdf", "odt"], "engine": "word", "header": "missing.tex"},
            base_dir=tmp_path,
        )
    text = "\n".join(e.value.errors)
    assert "「ext」" in text and "「engine」" in text and "「header」" in text


def test_cli_doc_conv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)
    args = _parse_cli_args(["watch", "--mode", "doc_conv", "--src", "docs", "--dst", "out",
                            "--ext", "pdf", "--ext", "html", "--engine", "pandoc"])
    task = _watch_config_from_cli(args).tasks[0]
    assert isinstance(task, DocConvTaskConfig)
    assert task.formats == ("pdf", "html")
    assert task.dst == (tmp_path / "out").resolve()


def test_cli_doc_conv_only_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "fig_src").mkdir()
    monkeypatch.chdir(tmp_path)
    args = _parse_cli_args(["watch", "--mode", "img_conv", "--engine", "pandoc"])
    with pytest.raises(ConfigError):
        _ = _watch_config_from_cli(args)


def test_browser_html_keeps_mermaid_block(tmp_path: Path) -> None:
    conv = DocConverter(tmp_path, tmp_path, output_formats=["html"])
    html = conv.build_browser_html("# T\n\n```mermaid\ngraph TD; A-->B\n```\n</script>")
    assert "graph TD; A-->B" in html
    assert "<\\/script>" in html  # md 中の </script> で script タグが閉じないこと


@needs_pandoc
def test_runner_keeps_folder_structure_and_skips_up_to_date(tmp_path: Path) -> None:
    src, dst = tmp_path / "src", tmp_path / "src" / "out"
    (src / "sub").mkdir(parents=True)
    md = src / "sub" / "a.md"
    md.write_text("# Hello\n\ntext\n", encoding="utf-8")
    (src / "sub" / "img.png").write_bytes(b"png")
    (src / "skip.txt").write_text("x", encoding="utf-8")

    task = DocConvTask(src, dst, output_formats=["html"], engine="pandoc", copy_exts=["png"])
    task.run_all_target_files_in_target_dir()

    out = dst / "sub" / "a.html"
    assert out.exists() and "Hello" in out.read_text(encoding="utf-8")
    assert (dst / "sub" / "img.png").exists()
    assert not (dst / "skip.html").exists()

    # 出力が新しければ変換しない / 古ければ変換する
    os.utime(out, (md.stat().st_mtime + 100, md.stat().st_mtime + 100))
    out.write_text("old", encoding="utf-8")
    os.utime(out, (md.stat().st_mtime + 100, md.stat().st_mtime + 100))
    task.run(md)
    assert out.read_text(encoding="utf-8") == "old"
    os.utime(out, (md.stat().st_mtime - 100, md.stat().st_mtime - 100))
    task.run(md)
    assert "Hello" in out.read_text(encoding="utf-8")

    # dst（src の中）にあるファイルは入力として扱わない
    (dst / "sub" / "b.md").write_text("# B\n", encoding="utf-8")
    task.run_all_target_files_in_target_dir()
    assert not (dst / "out").exists()


@needs_pandoc
def test_docx_output(tmp_path: Path) -> None:
    md = tmp_path / "a.md"
    md.write_text("# Hello\n", encoding="utf-8")
    assert DocConverter(tmp_path, tmp_path, output_formats=["docx"]).convert(md)
    assert (tmp_path / "a.docx").stat().st_size > 0
