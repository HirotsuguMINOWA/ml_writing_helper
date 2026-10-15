from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ml_writing_helper import main as main_mod
from ml_writing_helper.config import ConfigError, parse_config
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
    args = _parse_cli_args(["--mode", "doc_conv", "--src", "docs", "--monitor"])
    assert _watch_config_from_cli(args).monitor is True


def test_options_without_subcommand_are_the_watch_flow() -> None:
    """`ml_writing_helper --mode ...` (no subcommand) runs the former watch4ml flow."""
    args = _parse_cli_args(["--mode", "img_conv", "--ext", "pdf"])
    assert args.command is None
    assert _check_watch_args(args) == "mode"


def test_legacy_watch_token_is_ignored() -> None:
    """The former `watch` subcommand is accepted as a no-op alias."""
    args = _parse_cli_args(["watch", "--mode", "doc_conv", "--src", "docs", "--monitor"])
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
    assert "--monitor" in capsys.readouterr().out


def test_cli_monitor_usable_with_json() -> None:
    args = _parse_cli_args(["--json", "x.json", "--monitor"])
    assert _check_watch_args(args) == "json"


def test_cli_monitor_alone_is_error() -> None:
    args = _parse_cli_args(["--monitor"])
    with pytest.raises(ConfigError):
        _ = _check_watch_args(args)


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is not installed")
def test_without_monitor_runs_once_and_exits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def fail(*_args, **_kwargs):
        raise AssertionError("observer must not be built without --monitor")

    monkeypatch.setattr(main_mod, "_build_observer", fail)
    code = main_mod.main(["--mode", "doc_conv", "--src", "docs", "--dst", "out",
                          "--ext", "html", "--engine", "pandoc"])
    assert code == 0
    assert (tmp_path / "out" / "a.html").exists()
