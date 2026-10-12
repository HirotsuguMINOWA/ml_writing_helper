"""Watch task configuration loaded from ml_writing_helper.json.

Example::

    {
      "root": ".",
      "observer": "polling",
      "sleep_sec": 1.0,
      "log_level": "INFO",
      "tasks": [
        {"type": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf", "gray": false, "crop": true},
        {"type": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "exts": ["bib"], "diff_sec": 10}
      ]
    }

Relative paths are resolved from ``root``, which is itself resolved from the directory of the json file.

A single task can also be written at the top level with ``mode`` (shorthand, e.g. for ``--json '{...}'``)::

    {"mode": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "ext": "bib"}

``mode`` is accepted as an alias of ``type``, and ``ext`` as an alias of ``exts`` in copy tasks.
"""
import difflib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from ml_writing_helper.converter.slide_img_converter import ImgConvOutputType

CONFIG_FILENAME: Final[str] = "ml_writing_helper.json"
OUTPUT_FORMATS: Final[list[str]] = [str(x) for x in ImgConvOutputType]
LOG_LEVELS: Final[list[str]] = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
TASK_TYPES: Final[tuple[str, ...]] = ("img_conv", "copy")

DEFAULT_OBSERVER: Final[str] = "polling"
DEFAULT_SLEEP_SEC: Final[float] = 1.0
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_DIFF_SEC: Final[int] = 10
DEFAULT_COPY_EXTS: Final[tuple[str, ...]] = ("bib",)


class ConfigError(ValueError):
    """Invalid config, written for end users.

    ``errors`` holds every problem found (each may span several lines),
    ``title`` says what failed and ``hint`` what to do next. Use ``format_config_error`` to print it.
    """

    def __init__(self, errors: Sequence[str], title: str = "", hint: str = "") -> None:
        self.errors: list[str] = list(errors)
        self.title: str = title
        self.hint: str = hint
        super().__init__("\n".join(self.errors))


def format_config_error(e: ConfigError) -> str:
    """Render ConfigError as a readable block for the terminal."""
    lines = [f"エラー: {e.title or '設定に問題があります'}", ""]
    for msg in e.errors:
        first, *rest = msg.split("\n")
        lines.append(f"  ✗ {first}")
        lines.extend(f"      {r}" for r in rest)
    if e.hint:
        lines.append("")
        lines.extend(f"ヒント: {h}" if i == 0 else f"        {h}" for i, h in enumerate(e.hint.split("\n")))
    return "\n".join(lines)


@dataclass(frozen=True)
class ImgConvTaskConfig:
    src: Path
    dst: Path
    ext: str
    gray: bool = False
    crop: bool = True


@dataclass(frozen=True)
class CopyTaskConfig:
    src: Path
    dst: Path
    exts: tuple[str, ...] = DEFAULT_COPY_EXTS
    diff_sec: int = DEFAULT_DIFF_SEC


@dataclass
class WatchConfig:
    tasks: list[ImgConvTaskConfig | CopyTaskConfig] = field(default_factory=list)
    observer: str = DEFAULT_OBSERVER
    sleep_sec: float = DEFAULT_SLEEP_SEC
    log_level: str = DEFAULT_LOG_LEVEL


def strip_dot(ext: str) -> str:
    return ext.strip().lstrip(".").lower()


def resolve_path(path: str | Path, base: Path) -> Path:
    path_pl = Path(path).expanduser()
    if not path_pl.is_absolute():
        path_pl = base.joinpath(path_pl)
    return path_pl.resolve()


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _show(v: Any) -> str:
    """Show a user-given value as it looks in JSON."""
    return json.dumps(v, ensure_ascii=False)


def _choices(values: Sequence[str]) -> str:
    return ", ".join(values)


_TOP_KEYS: Final[tuple[str, ...]] = ("root", "observer", "sleep_sec", "log_level", "tasks")
_TASK_KEYS: Final[dict[str, tuple[str, ...]]] = {
    "img_conv": ("type", "mode", "src", "dst", "ext", "gray", "crop"),
    "copy": ("type", "mode", "src", "dst", "exts", "ext", "diff_sec"),
}
_TASK_KEYS_ANY: Final[tuple[str, ...]] = tuple(dict.fromkeys(k for keys in _TASK_KEYS.values() for k in keys))
_EXAMPLE: Final[str] = '{"mode": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf"}'


def _unknown_key_message(key: str, allowed: Sequence[str], where: str) -> str:
    near = difflib.get_close_matches(key, allowed, n=1)
    suggestion = f"「{near[0]}」の書き間違いではありませんか？" if near else f"使える項目: {_choices(allowed)}"
    return f"{where}「{key}」という項目はありません。{suggestion}"


def _dir_problem(label: str, given: str, resolved: Path) -> str | None:
    if resolved.is_dir():
        return None
    reason = "フォルダではなくファイルです" if resolved.exists() else "フォルダが見つかりません"
    return f"{label}{reason}\n指定値: {_show(given)}\n探した場所: {resolved}"


def _parse_task(
        t: Any,
        where: str,
        root: Path,
        check_paths: bool,
        errors: list[str],
) -> ImgConvTaskConfig | CopyTaskConfig | None:
    """Validate one task. Appends problems to errors and returns None if any."""
    n_errors = len(errors)
    if not isinstance(t, dict):
        errors.append(f"{where}は {{ }} で囲んで書いてください（例: {_EXAMPLE}）")
        return None

    task_type = t.get("type", t.get("mode"))
    if task_type is None:
        errors.append(f"{where}: 「mode」がありません。{_choices(TASK_TYPES)} のどれかを指定してください")
        return None
    if task_type not in TASK_TYPES:
        errors.append(
            f"{where}: 「mode」には {_choices(TASK_TYPES)} のどれかを指定してください（指定値: {_show(task_type)}）"
        )
        return None

    for key in t:
        if key not in _TASK_KEYS[task_type] and key not in _TOP_KEYS:
            errors.append(_unknown_key_message(key, _TASK_KEYS[task_type], f"{where}（{task_type}）: "))

    paths: dict[str, Path] = {}
    labels = {"src": "監視するフォルダ", "dst": "出力先のフォルダ"}
    for key in ("src", "dst"):
        v = t.get(key)
        if v is None:
            errors.append(f"{where}: 「{key}」（{labels[key]}）を指定してください")
        elif not isinstance(v, str) or not v.strip():
            errors.append(f"{where}: 「{key}」（{labels[key]}）はパスを文字列で指定してください（指定値: {_show(v)}）")
        else:
            paths[key] = resolve_path(v, root)
    if "src" in paths and check_paths:
        problem = _dir_problem(f"{where}: 「src」の", t["src"], paths["src"])
        if problem:
            errors.append(problem)

    if task_type == "img_conv":
        ext = t.get("ext", "pdf")
        if not isinstance(ext, str) or strip_dot(ext) not in OUTPUT_FORMATS:
            errors.append(f"{where}: 「ext」には {_choices(OUTPUT_FORMATS)} のどれかを指定してください（指定値: {_show(ext)}）")
        for key, default in (("gray", False), ("crop", True)):
            v = t.get(key, default)
            if not isinstance(v, bool):
                errors.append(f"{where}: 「{key}」には true か false を指定してください（指定値: {_show(v)}）")
        if len(errors) > n_errors:
            return None
        return ImgConvTaskConfig(
            src=paths["src"], dst=paths["dst"], ext=strip_dot(ext), gray=t.get("gray", False), crop=t.get("crop", True)
        )

    exts_key = "exts" if "exts" in t else "ext"
    exts = t.get(exts_key, list(DEFAULT_COPY_EXTS))
    if isinstance(exts, str):
        exts = [exts]
    if (
            not isinstance(exts, list)
            or not exts
            or not all(isinstance(e, str) and strip_dot(e) for e in exts)
    ):
        errors.append(
            f'{where}: 「{exts_key}」にはコピーする拡張子を "bib" や ["bib", "txt"] の形で指定してください'
            f"（指定値: {_show(exts)}）"
        )
    diff_sec = t.get("diff_sec", DEFAULT_DIFF_SEC)
    if not isinstance(diff_sec, int) or isinstance(diff_sec, bool) or diff_sec < 0:
        errors.append(f"{where}: 「diff_sec」には 0 以上の整数（秒）を指定してください（指定値: {_show(diff_sec)}）")
    if len(errors) > n_errors:
        return None
    return CopyTaskConfig(
        src=paths["src"], dst=paths["dst"], exts=tuple(strip_dot(e) for e in exts), diff_sec=diff_sec
    )


def parse_config(
        data: Any,
        base_dir: Path,
        available_observers: Sequence[str] | None = None,
        check_paths: bool = True,
) -> WatchConfig:
    """Validate a json-decoded config and build WatchConfig. Raises ConfigError listing all problems."""
    if isinstance(data, list):
        raise ConfigError(['タスクの一覧 [ ... ] は {"tasks": [ ... ]} のように「tasks」の中に書いてください'])
    if not isinstance(data, dict):
        raise ConfigError([f"設定全体を {{ }} で囲んで書いてください（例: {_EXAMPLE}）"])

    errors: list[str] = []
    is_shorthand = "tasks" not in data and ("mode" in data or "type" in data)
    if not is_shorthand:
        for key in data:
            if key not in _TOP_KEYS:
                allowed = _TOP_KEYS if key not in _TASK_KEYS_ANY else ()
                if allowed:
                    errors.append(_unknown_key_message(key, allowed, ""))
                else:
                    errors.append(
                        f"「{key}」はタスクの項目です。「tasks」の中の各タスクに書くか、"
                        f"1つのタスクだけなら「mode」も一緒にトップレベルへ書いてください"
                    )

    root_raw = data.get("root", ".")
    if not isinstance(root_raw, str) or not root_raw.strip():
        errors.append(f"「root」はフォルダのパスを文字列で指定してください（指定値: {_show(root_raw)}）")
        root_raw = "."
    root = resolve_path(root_raw, base_dir)
    if check_paths:
        problem = _dir_problem("「root」の", root_raw, root)
        if problem:
            errors.append(problem)

    observer = data.get("observer", DEFAULT_OBSERVER)
    if not isinstance(observer, str) or (
            available_observers is not None and observer not in available_observers
    ):
        errors.append(
            f"「observer」には {_choices(available_observers or [DEFAULT_OBSERVER])} のどれかを指定してください"
            f"（指定値: {_show(observer)}）"
        )

    sleep_sec = data.get("sleep_sec", DEFAULT_SLEEP_SEC)
    if not _is_number(sleep_sec) or sleep_sec <= 0:
        errors.append(f"「sleep_sec」には 0 より大きい数値（秒）を指定してください（指定値: {_show(sleep_sec)}）")
        sleep_sec = DEFAULT_SLEEP_SEC

    log_level = data.get("log_level", DEFAULT_LOG_LEVEL)
    if not isinstance(log_level, str) or log_level.upper() not in LOG_LEVELS:
        errors.append(f"「log_level」には {_choices(LOG_LEVELS)} のどれかを指定してください（指定値: {_show(log_level)}）")
        log_level = DEFAULT_LOG_LEVEL

    tasks: list[ImgConvTaskConfig | CopyTaskConfig] = []
    if is_shorthand:
        task = _parse_task(data, "タスク", root, check_paths, errors)
        if task is not None:
            tasks.append(task)
    else:
        tasks_raw = data.get("tasks")
        if tasks_raw is None or tasks_raw == []:
            errors.append(
                "実行するタスクがありません。「tasks」にタスクを書いてください\n"
                f'例: {{"tasks": [{_EXAMPLE}]}}'
            )
        elif not isinstance(tasks_raw, list):
            errors.append(f"「tasks」はタスクを [ ] で囲んだ一覧にしてください（例: [{_EXAMPLE}]）")
        else:
            for i, t in enumerate(tasks_raw):
                task = _parse_task(t, f"{i + 1}番目のタスク", root, check_paths, errors)
                if task is not None:
                    tasks.append(task)

    if errors:
        raise ConfigError(errors)
    return WatchConfig(tasks=tasks, observer=observer, sleep_sec=float(sleep_sec), log_level=log_level.upper())


_JSON_REASONS: Final[tuple[tuple[str, str], ...]] = (
    ("Illegal trailing comma", "最後の項目の後ろに余分なカンマ , があります。削除してください"),
    ("Expecting property name enclosed in double quotes",
     "項目名はダブルクォート \" で囲んでください（シングルクォート ' や、最後の項目の後ろの余分なカンマ , が原因のことが多いです）"),
    ("Expecting ',' delimiter", "項目と項目の間のカンマ , が足りないか、カッコ } ] の閉じ忘れがあります"),
    ("Expecting ':' delimiter", "項目名と値の間のコロン : が足りません"),
    ("Expecting value",
     "値がありません（空のファイル、最後の項目の後ろの余分なカンマ ,、"
     "true / false / null の綴り間違い、文字列を \" で囲み忘れ、などが原因のことが多いです）"),
    ("Unterminated string", "文字列を閉じるダブルクォート \" がありません"),
    ("Extra data", "JSON の終わりの後ろに余分な文字があります（{ } が2つ並んでいる、など）"),
    ("Invalid control character", "文字列の中に改行やタブがそのまま入っています"),
    ("Invalid \\escape", "バックスラッシュ \\ の書き方が正しくありません（Windows のパスは / か \\\\ で区切ってください）"),
)


def _json_syntax_error(e: json.JSONDecodeError, title: str, is_inline: bool) -> ConfigError:
    reason = next((ja for en, ja in _JSON_REASONS if e.msg.startswith(en)), e.msg)
    detail = f"{e.lineno}行目 {e.colno}文字目: {reason}"
    lines = e.doc.splitlines()
    if 0 < e.lineno <= len(lines):
        line = lines[e.lineno - 1]
        detail += f"\n{line}\n{' ' * (e.colno - 1)}^ ここ"
    hint = "JSON の書き方は ReadMe の「json instruction」を参照してください"
    if is_inline:
        hint = (
            "JSON 文字列は全体をシングルクォートで囲んでください。囲まないとシェルが \" を消してしまいます\n"
            f"例: watch4ml --json '{_EXAMPLE}'"
        )
    return ConfigError([detail], title=title, hint=hint)


def load_config(path: Path, available_observers: Sequence[str] | None = None) -> WatchConfig:
    title = f"設定ファイルを読み込めませんでした（{path}）"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ConfigError([f"ファイルが見つかりません: {path}"], title=title) from e
    except IsADirectoryError as e:
        raise ConfigError([f"フォルダが指定されています: {path}"], title=title,
                          hint=f"json ファイル（例: {path / CONFIG_FILENAME}）を指定してください") from e
    except PermissionError as e:
        raise ConfigError([f"ファイルを読む権限がありません: {path}"], title=title) from e
    except UnicodeDecodeError as e:
        raise ConfigError(["文字コードが UTF-8 ではありません"], title=title,
                          hint="エディタで文字コードを UTF-8 にして保存し直してください") from e
    if not text.strip():
        raise ConfigError(["ファイルが空です"], title=title,
                          hint=f"例: {{\"tasks\": [{_EXAMPLE}]}}\n"
                               "ファイルを削除して watch4ml を引数なしで実行すると、Web UI で作成できます")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise _json_syntax_error(e, title=f"設定ファイルの JSON の書き方に誤りがあります（{path}）", is_inline=False) from e
    try:
        return parse_config(data, base_dir=path.parent, available_observers=available_observers)
    except ConfigError as e:
        raise ConfigError(e.errors, title=f"設定ファイルの内容に誤りがあります（{path}）",
                          hint="相対パスは、設定ファイルのあるフォルダ（「root」）を基準に探します") from e


def looks_like_json(value: str) -> bool:
    """True if a --json value is an inline JSON object rather than a file path."""
    return value.lstrip().startswith("{")


def load_config_string(text: str, base_dir: Path, available_observers: Sequence[str] | None = None) -> WatchConfig:
    """Load config from an inline JSON string. Relative paths are resolved from base_dir."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise _json_syntax_error(e, title="--json に渡した JSON 文字列の書き方に誤りがあります", is_inline=True) from e
    try:
        return parse_config(data, base_dir=base_dir, available_observers=available_observers)
    except ConfigError as e:
        raise ConfigError(e.errors, title="--json に渡した JSON 文字列の内容に誤りがあります",
                          hint=f"相対パスは、今いるフォルダ（{base_dir}）を基準に探します") from e


def load_config_arg(value: str, cwd: Path, available_observers: Sequence[str] | None = None) -> WatchConfig:
    """Load config from a --json value: an inline JSON string or a json file path."""
    if looks_like_json(value):
        return load_config_string(value, base_dir=cwd, available_observers=available_observers)
    path = resolve_path(value, cwd)
    if not path.exists():
        stripped = value.strip()
        if stripped.startswith("[") or '"' in stripped or (":" in stripped and not Path(stripped).anchor):
            hint = (
                "JSON 文字列を渡すつもりなら、{ } で囲み、全体をシングルクォートで囲んでください\n"
                f"例: watch4ml --json '{_EXAMPLE}'"
            )
        else:
            hint = (
                "ファイル名の綴りと、今いるフォルダを確認してください\n"
                f"ファイルを作るには、{CONFIG_FILENAME} の無いフォルダで watch4ml を引数なしで実行すると Web UI が開きます"
            )
        raise ConfigError(
            [f"ファイルが見つかりません\n指定値: {_show(value)}\n探した場所: {path}"],
            title="--json で指定したファイルが見つかりません",
            hint=hint,
        )
    return load_config(path, available_observers=available_observers)
