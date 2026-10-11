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
"""
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
    """Invalid config. ``errors`` holds every problem found."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors: list[str] = list(errors)
        super().__init__("\n".join(self.errors))


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


def parse_config(
        data: Any,
        base_dir: Path,
        available_observers: Sequence[str] | None = None,
        check_paths: bool = True,
) -> WatchConfig:
    """Validate a json-decoded config and build WatchConfig. Raises ConfigError listing all problems."""
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ConfigError(["top level must be a JSON object"])

    root_raw = data.get("root", ".")
    if not isinstance(root_raw, str) or not root_raw.strip():
        errors.append('"root" must be a non-empty string')
        root_raw = "."
    root = resolve_path(root_raw, base_dir)
    if check_paths and not root.is_dir():
        errors.append(f'"root" is not a directory: {root}')

    observer = data.get("observer", DEFAULT_OBSERVER)
    if not isinstance(observer, str) or (
            available_observers is not None and observer not in available_observers
    ):
        errors.append(f'"observer" must be one of {list(available_observers or [])}: {observer!r}')

    sleep_sec = data.get("sleep_sec", DEFAULT_SLEEP_SEC)
    if not _is_number(sleep_sec) or sleep_sec <= 0:
        errors.append(f'"sleep_sec" must be a positive number: {sleep_sec!r}')

    log_level = data.get("log_level", DEFAULT_LOG_LEVEL)
    if not isinstance(log_level, str) or log_level.upper() not in LOG_LEVELS:
        errors.append(f'"log_level" must be one of {LOG_LEVELS}: {log_level!r}')
        log_level = DEFAULT_LOG_LEVEL

    tasks_raw = data.get("tasks")
    tasks: list[ImgConvTaskConfig | CopyTaskConfig] = []
    if not isinstance(tasks_raw, list) or not tasks_raw:
        errors.append('"tasks" must be a non-empty list')
        tasks_raw = []

    for i, t in enumerate(tasks_raw):
        where = f"tasks[{i}]"
        if not isinstance(t, dict):
            errors.append(f"{where} must be an object")
            continue
        task_type = t.get("type")
        if task_type not in TASK_TYPES:
            errors.append(f'{where}.type must be one of {list(TASK_TYPES)}: {task_type!r}')
            continue

        paths: dict[str, Path] = {}
        for key in ("src", "dst"):
            v = t.get(key)
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{where}.{key} is required (string)")
            else:
                paths[key] = resolve_path(v, root)
        if "src" in paths and check_paths and not paths["src"].is_dir():
            errors.append(f"{where}.src is not a directory: {paths['src']}")
        if len(paths) != 2:
            continue

        if task_type == "img_conv":
            ext = t.get("ext", "pdf")
            if not isinstance(ext, str) or strip_dot(ext) not in OUTPUT_FORMATS:
                errors.append(f"{where}.ext must be one of {OUTPUT_FORMATS}: {ext!r}")
                continue
            gray = t.get("gray", False)
            crop = t.get("crop", True)
            if not isinstance(gray, bool) or not isinstance(crop, bool):
                errors.append(f"{where}.gray / crop must be true or false")
                continue
            tasks.append(ImgConvTaskConfig(src=paths["src"], dst=paths["dst"], ext=strip_dot(ext), gray=gray, crop=crop))
        else:
            exts = t.get("exts", list(DEFAULT_COPY_EXTS))
            if isinstance(exts, str):
                exts = [exts]
            if (
                    not isinstance(exts, list)
                    or not exts
                    or not all(isinstance(e, str) and strip_dot(e) for e in exts)
            ):
                errors.append(f"{where}.exts must be a non-empty list of extensions: {exts!r}")
                continue
            diff_sec = t.get("diff_sec", DEFAULT_DIFF_SEC)
            if not isinstance(diff_sec, int) or isinstance(diff_sec, bool) or diff_sec < 0:
                errors.append(f"{where}.diff_sec must be a non-negative integer: {diff_sec!r}")
                continue
            tasks.append(
                CopyTaskConfig(
                    src=paths["src"],
                    dst=paths["dst"],
                    exts=tuple(strip_dot(e) for e in exts),
                    diff_sec=diff_sec,
                )
            )

    if errors:
        raise ConfigError(errors)
    return WatchConfig(tasks=tasks, observer=observer, sleep_sec=float(sleep_sec), log_level=log_level.upper())


def load_config(path: Path, available_observers: Sequence[str] | None = None) -> WatchConfig:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError([f"{path}: invalid JSON ({e})"]) from e
    try:
        return parse_config(data, base_dir=path.parent, available_observers=available_observers)
    except ConfigError as e:
        raise ConfigError([f"{path}: {msg}" for msg in e.errors]) from e
