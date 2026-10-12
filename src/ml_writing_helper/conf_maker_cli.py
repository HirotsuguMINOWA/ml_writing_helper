"""Interactive terminal wizard to create ml_writing_helper.json.

Each answer is checked right away (choices, numbers, folder existence) and asked again if invalid.
The finished config is validated with ``parse_config`` before saving.
"""
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ml_writing_helper.config import (
    DEFAULT_COPY_EXTS,
    DEFAULT_DIFF_SEC,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OBSERVER,
    DEFAULT_SLEEP_SEC,
    LOG_LEVELS,
    OUTPUT_FORMATS,
    TASK_TYPES,
    ConfigError,
    ConfMakerResult,
    format_config_error,
    parse_config,
    read_existing_config,
    resolve_path,
    strip_dot,
)

InputFn = Callable[[str], str]
PrintFn = Callable[..., None]


class _Wizard:
    def __init__(self, input_fn: InputFn, print_fn: PrintFn) -> None:
        self._input = input_fn
        self._print = print_fn

    def ask(self, label: str, default: str | None = None, check: Callable[[str], str | None] | None = None) -> str:
        """Ask until a valid answer. ``check`` returns an error message or None."""
        suffix = f" [{default}]" if default not in (None, "") else ""
        while True:
            answer = self._input(f"  {label}{suffix}: ").strip()
            if answer == "" and default is not None:
                answer = default
            if answer == "":
                self._print("    → 入力してください")
                continue
            problem = check(answer) if check else None
            if problem is None:
                return answer
            self._print(f"    → {problem}")

    def choose(self, label: str, choices: Sequence[str], default: str) -> str:
        return self.ask(
            f"{label} ({' / '.join(choices)})",
            default,
            lambda a: None if a in choices else f"{', '.join(choices)} のどれかを入力してください",
        )

    def yes_no(self, label: str, default: bool) -> bool:
        answer = self.ask(
            f"{label} (y/n)",
            "y" if default else "n",
            lambda a: None if a.lower() in ("y", "yes", "n", "no") else "y か n を入力してください",
        )
        return answer.lower() in ("y", "yes")


def _check_number(positive: bool, integer: bool) -> Callable[[str], str | None]:
    def check(a: str) -> str | None:
        try:
            v = int(a) if integer else float(a)
        except ValueError:
            return "整数を入力してください" if integer else "数値を入力してください"
        if positive and v <= 0:
            return "0 より大きい値を入力してください"
        if v < 0:
            return "0 以上の値を入力してください"
        return None
    return check


def _check_dir(base: Path) -> Callable[[str], str | None]:
    def check(a: str) -> str | None:
        p = resolve_path(a, base)
        if p.is_dir():
            return None
        reason = "フォルダではなくファイルです" if p.exists() else "フォルダが見つかりません"
        return f"{reason}: {p}"
    return check


def _check_exts(a: str) -> str | None:
    exts = [strip_dot(e) for e in a.split(",")]
    return None if exts and all(exts) else '拡張子をカンマ区切りで入力してください（例: bib, txt）'


def _ask_task(w: _Wizard, root: Path, prev: dict[str, Any] | None) -> dict[str, Any]:
    prev = prev or {}
    prev_type = prev.get("type", prev.get("mode"))
    mode = w.choose("mode", TASK_TYPES, prev_type if prev_type in TASK_TYPES else "img_conv")
    same = prev_type == mode
    if mode == "img_conv":
        return {
            "type": "img_conv",
            "src": w.ask("src（監視するフォルダ）", prev.get("src", "fig_src") if same else "fig_src", _check_dir(root)),
            "dst": w.ask("dst（出力先のフォルダ。無ければ作成）", prev.get("dst", "fig_gen") if same else "fig_gen"),
            "ext": strip_dot(w.choose("ext（出力形式）", OUTPUT_FORMATS, strip_dot(str(prev.get("ext", "pdf"))) if same else "pdf")),
            "gray": w.yes_no("gray（グレー化する）", bool(prev.get("gray", False)) if same else False),
            "crop": w.yes_no("crop（余白を切り取る）", bool(prev.get("crop", True)) if same else True),
        }
    prev_exts = prev.get("exts", prev.get("ext", list(DEFAULT_COPY_EXTS))) if same else list(DEFAULT_COPY_EXTS)
    if isinstance(prev_exts, str):
        prev_exts = [prev_exts]
    src = w.ask("src（監視するフォルダ）", prev.get("src") if same else None, _check_dir(root))
    dst = w.ask("dst（コピー先のフォルダ。無ければ作成）", prev.get("dst") if same else None)
    exts = w.ask("ext（コピーする拡張子。カンマ区切り）", ", ".join(map(str, prev_exts)), _check_exts)
    return {
        "type": "copy",
        "src": src,
        "dst": dst,
        "exts": [strip_dot(e) for e in exts.split(",")],
        "diff_sec": int(w.ask(
            "diff_sec（更新時刻の差がこの秒数以下ならコピーしない）",
            str(prev.get("diff_sec", DEFAULT_DIFF_SEC)) if same else str(DEFAULT_DIFF_SEC),
            _check_number(positive=False, integer=True),
        )),
    }


def run_cli_maker(
        save_path: Path,
        available_observers: Sequence[str],
        input_fn: InputFn = input,
        print_fn: PrintFn = print,
) -> ConfMakerResult:
    """Create the config interactively in the terminal. Blocks until saved or cancelled."""
    w = _Wizard(input_fn, print_fn)
    try:
        return _run(w, save_path, available_observers, print_fn)
    except (KeyboardInterrupt, EOFError):
        print_fn("\n中止しました。ファイルは保存していません。")
        return ConfMakerResult(saved=False, start_watch=False)


def _run(w: _Wizard, save_path: Path, observers: Sequence[str], print_fn: PrintFn) -> ConfMakerResult:
    print_fn(f"設定ファイルを作成します: {save_path}")
    print_fn("[ ] 内は既定値です。Enter だけでその値になります。Ctrl+C で中止します。")
    existing = read_existing_config(save_path) if save_path.exists() else None
    if save_path.exists():
        if existing is not None:
            print_fn("既存のファイルがあります。その内容を既定値として表示します。保存すると上書きされます。")
        else:
            print_fn("既存のファイルがありますが読み込めませんでした。保存すると上書きされます。")
        if not w.yes_no("続けますか", True):
            print_fn("中止しました。ファイルは変更していません。")
            return ConfMakerResult(saved=False, start_watch=False)
    existing = existing or {}
    base_dir = save_path.parent

    print_fn("\n[全体設定]")
    root_raw = w.ask("root（相対パスの基準フォルダ）", str(existing.get("root", ".")), _check_dir(base_dir))
    root = resolve_path(root_raw, base_dir)
    prev_observer = existing.get("observer", DEFAULT_OBSERVER)
    observer = w.choose("observer", observers, prev_observer if prev_observer in observers else DEFAULT_OBSERVER)
    sleep_sec = float(w.ask("sleep_sec（秒）", str(existing.get("sleep_sec", DEFAULT_SLEEP_SEC)),
                            _check_number(positive=True, integer=False)))
    prev_level = str(existing.get("log_level", DEFAULT_LOG_LEVEL)).upper()
    log_level = w.choose("log_level", LOG_LEVELS, prev_level if prev_level in LOG_LEVELS else DEFAULT_LOG_LEVEL).upper()

    prev_tasks: list[Any] = list(existing.get("tasks", []))
    tasks: list[dict[str, Any]] = []
    while True:
        prev = prev_tasks[len(tasks)] if len(tasks) < len(prev_tasks) and isinstance(prev_tasks[len(tasks)], dict) else None
        print_fn(f"\n[{len(tasks) + 1}番目のタスク]")
        tasks.append(_ask_task(w, root, prev))
        print_fn()
        if not w.yes_no("別のタスクを追加しますか", len(tasks) < len(prev_tasks)):
            break

    config: dict[str, Any] = {
        "root": root_raw,
        "observer": observer,
        "sleep_sec": sleep_sec,
        "log_level": log_level,
        "tasks": tasks,
    }
    print_fn("\n[作成した設定]")
    print_fn(json.dumps(config, ensure_ascii=False, indent=2))

    try:
        _ = parse_config(config, base_dir=base_dir, available_observers=observers)
    except ConfigError as e:
        e.title = "作成した設定に問題があります。保存しませんでした"
        print_fn(format_config_error(e))
        return ConfMakerResult(saved=False, start_watch=False)

    print_fn()
    if not w.yes_no(f"{save_path} に保存しますか", True):
        print_fn("保存しませんでした。")
        return ConfMakerResult(saved=False, start_watch=False)
    save_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_fn(f"保存しました: {save_path}")
    start = w.yes_no("この設定で監視を開始しますか", True)
    return ConfMakerResult(saved=True, start_watch=start)
