from __future__ import annotations

import shutil
import urllib.error
from pathlib import Path

import pytest
from loguru import logger

from ml_writing_helper import dst_sync, link_checker
from ml_writing_helper import main as main_mod
from ml_writing_helper.link_checker import check_links
from ml_writing_helper.task_runner.copy_runner import CopyTask
from ml_writing_helper.config import (
    ConfigError,
    CopyTaskConfig,
    DocConvTaskConfig,
    ImgConvTaskConfig,
    ScormTaskConfig,
    parse_config,
    validate_task_paths,
)
from ml_writing_helper.main import _check_watch_args, _parse_cli_args, _watch_config_from_cli


def test_json_monitor_default_false(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    assert parse_config({"mode": "doc_conv", "src": "docs"}, base_dir=tmp_path).monitor is False
    assert parse_config({"mode": "doc_conv", "src": "docs", "monitor": True}, base_dir=tmp_path).monitor is True


def test_json_monitor_must_be_bool(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    with pytest.raises(ConfigError) as e:
        _ = parse_config({"mode": "doc_conv", "src": "docs", "monitor": "yes"}, base_dir=tmp_path)
    assert "「monitor」" in e.value.errors[0]


def test_cli_monitor_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)
    args = _parse_cli_args(["--mode", "doc_conv", "--src", "docs"])
    assert _watch_config_from_cli(args).monitor is False
    args = _parse_cli_args(["--mode", "doc_conv", "--src", "docs", "--watch"])
    assert _watch_config_from_cli(args).monitor is True


def test_options_without_subcommand_are_the_watch_flow() -> None:
    """`ml_writing_helper --mode ...` (no subcommand) runs the former watch4ml flow."""
    args = _parse_cli_args(["--mode", "img_conv", "--ext", "pdf"])
    assert args.command is None
    assert _check_watch_args(args) == "mode"


def test_legacy_watch_token_is_ignored() -> None:
    """The former `watch` subcommand is accepted as a no-op alias."""
    args = _parse_cli_args(["watch", "--mode", "doc_conv", "--src", "docs", "--watch"])
    assert args.command is None
    assert args.mode == "doc_conv" and args.monitor is True


@pytest.mark.parametrize("argv", [["convert", "a.pptx", "out", "pdf"], ["a.pptx", "out", "pdf"]])
def test_convert_subcommand_with_and_without_its_name(argv: list[str]) -> None:
    """`convert` keeps working with the name omitted, as the former convert4ml did."""
    args = _parse_cli_args(argv)
    assert args.command == "convert"
    assert (args.src_path, args.dst_dir_apath, args.to_fmt) == ("a.pptx", "out", "pdf")


def test_monitor_subcommand_is_kept() -> None:
    args = _parse_cli_args(["monitor", "src", "dst", "png"])
    assert args.command == "monitor"
    assert (args.src_dir, args.dst_dir, args.to_fmt) == ("src", "dst", "png")


def test_no_argument_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main_mod.main([]) == 0
    assert "--watch" in capsys.readouterr().out


def test_cli_monitor_usable_with_json() -> None:
    args = _parse_cli_args(["--json", "x.json", "--watch"])
    assert _check_watch_args(args) == "json"


def test_cli_monitor_alone_is_error() -> None:
    args = _parse_cli_args(["--watch"])
    with pytest.raises(ConfigError):
        _ = _check_watch_args(args)


def _touch(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


def _fake_stdin(monkeypatch: pytest.MonkeyPatch, answer: str | None) -> None:
    """answer が None なら端末でない stdin、文字列なら端末として確認プロンプトにその答えを返す。"""

    class _Stdin:
        def isatty(self) -> bool:
            return answer is not None

    monkeypatch.setattr(dst_sync.sys, "stdin", _Stdin())
    monkeypatch.setattr("builtins.input", lambda _prompt="": answer or "")


def test_copy_sync_dst_deletes_only_dst_files_missing_in_src(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    _touch(src / "a.bib")
    _touch(src / "sub" / "b.bib")
    _touch(dst / "a.bib", "old")
    _touch(dst / "old.bib")
    _touch(dst / "sub" / "old.bib")
    _fake_stdin(monkeypatch, "y")

    CopyTask(src_dir_path=src, dst_dir_path=dst, src_suffixes=["bib"], sync_dst=True).run_all_target_files_in_target_dir()

    assert (dst / "a.bib").exists() and (dst / "sub" / "b.bib").exists()
    assert not (dst / "old.bib").exists()
    assert not (dst / "sub" / "old.bib").exists()
    assert (src / "a.bib").exists() and (src / "sub" / "b.bib").exists()


def test_copy_sync_dst_keeps_extras_without_terminal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    _touch(src / "a.bib")
    _touch(dst / "old.bib")
    _fake_stdin(monkeypatch, None)

    CopyTask(src_dir_path=src, dst_dir_path=dst, src_suffixes=["bib"], sync_dst=True).run_all_target_files_in_target_dir()

    assert (dst / "old.bib").exists()


def test_sync_dst_refuses_same_src_and_dst(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    with pytest.raises(ConfigError):
        _ = parse_config({"mode": "copy", "src": "docs", "dst": "docs", "sync_dst": True}, base_dir=tmp_path)


def test_check_status_returns_final_status_after_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        status = 200

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(link_checker.urllib.request, "urlopen", lambda req, timeout: _Response())
    assert link_checker.check_status("https://example.com/moved") == 200


def test_check_links_warns_only_for_non_200(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    doc = tmp_path / "a.md"
    _ = doc.write_text("[ok](https://ok.example/)\n[ng](https://ng.example/)\n", encoding="utf-8")

    class _Response:
        status = 200

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    def fake_urlopen(req: object, timeout: float) -> _Response:
        if "ng.example" in req.full_url:  # type: ignore[attr-defined]
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", None, None)  # type: ignore[attr-defined]
        return _Response()

    monkeypatch.setattr(link_checker.urllib.request, "urlopen", fake_urlopen)
    warnings: list[str] = []
    handler_id = logger.add(lambda m: warnings.append(m.record["message"]), level="WARNING")
    try:
        check_links(doc)
    finally:
        logger.remove(handler_id)

    assert len(warnings) == 1
    assert "https://ng.example/" in warnings[0] and "404" in warnings[0]


def test_cli_sync_dst_rejected_for_img_conv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)
    args = _parse_cli_args(["--mode", "img_conv", "--src", "docs", "--ext", "pdf", "--sync-dst"])
    with pytest.raises(ConfigError):
        _ = _watch_config_from_cli(args)


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is not installed")
def test_without_monitor_runs_once_and_exits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def fail(*_args, **_kwargs):
        raise AssertionError("observer must not be built without --watch")

    monkeypatch.setattr(main_mod, "_build_observer", fail)
    code = main_mod.main(["--mode", "doc_conv", "--src", "docs", "--dst", "out",
                          "--ext", "html", "--engine", "pandoc"])
    assert code == 0
    assert (tmp_path / "out" / "a.html").exists()


# ---------------------------- validate_task_paths ----------------------------


def test_validate_task_paths_src_missing_file(tmp_path: Path) -> None:
    src = tmp_path / "nothere.md"
    problems = validate_task_paths(ScormTaskConfig(src=src, dst=tmp_path, patterns=("*.md",)))
    assert any("src" in p and "ファイルが見つかりません" in p for p in problems)


def test_validate_task_paths_src_missing_dir(tmp_path: Path) -> None:
    src = tmp_path / "nothere"
    problems = validate_task_paths(CopyTaskConfig(src=src, dst=tmp_path))
    assert any("src" in p and "フォルダが見つかりません" in p for p in problems)


def test_validate_task_paths_copy_dst_missing(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    problems = validate_task_paths(CopyTaskConfig(src=tmp_path / "src", dst=tmp_path / "missing_dst"))
    assert any("dst" in p and "フォルダが見つかりません" in p for p in problems)


def test_validate_task_paths_non_copy_dst_missing_is_ok(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    # doc_conv / img_conv は dst がなくても OK（処理時に自動生成）
    assert validate_task_paths(DocConvTaskConfig(src=tmp_path / "src", dst=tmp_path / "out")) == []
    assert validate_task_paths(
        ImgConvTaskConfig(src=tmp_path / "src", dst=tmp_path / "out", ext="pdf")
    ) == []


def test_validate_task_paths_all_ok(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "dst").mkdir()
    assert validate_task_paths(CopyTaskConfig(src=tmp_path / "src", dst=tmp_path / "dst")) == []


# ---------------------------- parse_config / --mode への統合 ----------------------------


def test_parse_config_copy_missing_src_stops(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as e:
        _ = parse_config({"mode": "copy", "src": "no_src", "dst": "no_dst"}, base_dir=tmp_path)
    text = "\n".join(e.value.errors)
    assert "src" in text


def test_parse_config_copy_missing_dst_stops(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with pytest.raises(ConfigError) as e:
        _ = parse_config({"mode": "copy", "src": "src", "dst": "no_dst"}, base_dir=tmp_path)
    text = "\n".join(e.value.errors)
    assert "dst" in text


def test_parse_config_doc_conv_missing_dst_ok(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    config = parse_config({"mode": "doc_conv", "src": "docs"}, base_dir=tmp_path)
    assert isinstance(config.tasks[0], DocConvTaskConfig)


def test_parse_config_sync_dst_and_check_link_keys(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "dst").mkdir()
    copy_task = parse_config(
        {"mode": "copy", "src": "src", "dst": "dst", "sync_dst": True, "check_link": True}, base_dir=tmp_path
    ).tasks[0]
    assert (copy_task.sync_dst, copy_task.check_link) == (True, True)
    doc_task = parse_config({"mode": "doc_conv", "src": "src", "check_link": True}, base_dir=tmp_path).tasks[0]
    assert (doc_task.sync_dst, doc_task.check_link) == (False, True)


def test_cli_mode_copy_missing_src_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError):
        _ = _watch_config_from_cli(_parse_cli_args(["--mode", "copy", "--src", "no_src", "--dst", "dst"]))


def test_cli_mode_copy_missing_dst_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "src").mkdir()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError):
        _ = _watch_config_from_cli(_parse_cli_args(["--mode", "copy", "--src", "src", "--dst", "no_dst"]))


def test_cli_mode_img_conv_missing_dst_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "fig_src").mkdir()
    monkeypatch.chdir(tmp_path)
    config = _watch_config_from_cli(_parse_cli_args(["--mode", "img_conv", "--src", "fig_src"]))
    task = config.tasks[0]
    assert isinstance(task, ImgConvTaskConfig)
    # dst は自動的に fig_gen になる（存在しないこと）
    assert task.dst == (tmp_path / "fig_gen").resolve()
    assert not task.dst.exists()
