"""
Markdown の小テストを SCORM 1.2 パッケージ（.zip）へ変換する監視Task（scorm）
"""
from collections.abc import Sequence
from pathlib import Path
from typing import Final, override

from loguru import logger
from typed_classproperties import cached_classproperty
from watchdog.events import DirMovedEvent, FileMovedEvent

from ml_writing_helper.converter.doc_converter import normalize_input_patterns
from ml_writing_helper.converter.scorm12 import Scorm12Error, build_scorm12_package
from ml_writing_helper.enum_cls import TaskType
from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner

SCORM_OUTPUT_SUFFIX: Final[str] = "_scorm12.zip"
DEFAULT_SCORM_PATTERNS: Final[tuple[str, ...]] = ("*.md",)


class ScormTask(ABCTaskRunner):
    """監視下の Markdown 小テストが変更されたら SCORM 1.2 の ZIP を作る。

    - src がファイルなら、そのファイルだけを対象にする（監視するのは親フォルダ）。
    - src がフォルダなら、直下の patterns に合うファイルを対象にする。
    - dst が .zip ならそのパスへ（src がファイルのときだけ）、フォルダなら「<stem>_scorm12.zip」として出力する。
    """

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(src={self._src_file or self._src_dir_path}, dst_dir_path={self._dest_dir_path}, "
            f"patterns={self._patterns})"
        )

    def __init__(
            self,
            src_path: str | Path,
            dst_path: str | Path,
            patterns: Sequence[str] = DEFAULT_SCORM_PATTERNS,
            diff_sec: int = 10,
            wait_sec: int = 2,
    ):
        src_pl = Path(src_path)
        self._src_file: Final[Path | None] = src_pl if src_pl.is_file() else None
        super().__init__(
            src_dir_path=src_pl.parent if self._src_file else src_pl,
            dst_dir_path=dst_path,
            diff_sec=diff_sec,
            wait_sec=wait_sec,
            src_suffixes=["md"],
            dst_suffixes=["zip"],
        )
        self._patterns: Final[tuple[str, ...]] = tuple(patterns)
        self._regexes = normalize_input_patterns(self._patterns)

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.scorm

    def _is_target(self, path: Path) -> bool:
        if path.name.startswith(("~", ".")) or path.stem.endswith("~"):
            return False
        if self._src_file is not None:
            return path.resolve() == self._src_file.resolve()
        return path.parent.resolve() == self._src_dir_path.resolve() and any(
            r.fullmatch(path.name) for r in self._regexes
        )

    @override
    def dst_file_path(self, update_file_path: Path) -> Path:
        if self._dest_dir_path.suffix.lower() == ".zip":
            return self._dest_dir_path
        return self._dest_dir_path / (update_file_path.stem + SCORM_OUTPUT_SUFFIX)

    @override
    def run(self, update_file_path: Path, startup: bool = False) -> None:
        """SCORM パッケージが無いか古ければ作る。

        起動時は src が出力より diff_sec 秒を超えて新しいときだけ、監視中は src が出力より新しければ作る。
        """
        path = Path(update_file_path)
        if not path.is_file() or not self._is_target(path):
            return
        dst = self.dst_file_path(path)
        diff_sec = self._diff_sec if startup else 0
        if dst.exists() and path.stat().st_mtime - dst.stat().st_mtime <= diff_sec:
            logger.debug(f"Up-to-date: {path}")
            return
        try:
            _ = build_scorm12_package(path, dst)
        except Scorm12Error as e:
            logger.error(f"SCORM変換エラー: {path}: {e}")
            return
        except Exception as e:
            logger.exception(e)
            return
        logger.info(f"SCORM 1.2 package created: {path} → {dst}")

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        self.run(update_file_path)

    @override
    def run_all_target_files_in_target_dir(self) -> None:
        if self._src_file is not None:
            self.run(self._src_file, startup=True)
            return
        for path in sorted(self._src_dir_path.iterdir()):
            self.run(path, startup=True)

    @override
    def on_moved(self, event: FileMovedEvent | DirMovedEvent) -> None:
        # エディタの「一時ファイルに書いてリネーム」保存では、移動先が変更後のファイル
        if event.is_directory or isinstance(event.dest_path, bytes):
            return
        self.run(Path(event.dest_path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScormTask):
            return NotImplemented
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash((self.task_type, self._src_file, self._src_dir_path, self._dest_dir_path, self._patterns))
