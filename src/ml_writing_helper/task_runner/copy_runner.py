import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import override

from loguru import logger
from typed_classproperties import cached_classproperty

from src.ml_writing_helper.enum_cls import TaskType
from src.ml_writing_helper.task_runner.abc_runner import ABCTaskRunner


class CopyTask(ABCTaskRunner):
    def __init__(
            self,
            # task_type: TaskType,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            diff_sec: int = 10,
            wait_sec: int = 2,
            src_suffixes: Sequence[str] = [""],
            # dst_suffixes: Sequence[str] = [""]
            # observer:EventHandler=FileSystemEventHandler
    ):
        super().__init__(
            src_dir_path=src_dir_path,
            dst_dir_path=dst_dir_path,
            diff_sec=diff_sec,
            wait_sec=wait_sec,
            src_suffixes=src_suffixes,
            dst_suffixes=[""]
            # observer:EventHandler=FileSystemEventHandler
        )

    @cached_classproperty
    def target_src_suffixes(cls) -> Sequence[str]:
        return []

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.copy

    """監視下で.bibの様に変更があればcopyする処理をするクラス"""

    @override
    def dst_file_path(self, update_file_path: Path) -> Path:
        if self._dest_dir_path.suffix:
            return self._dest_dir_path
        return self._dest_dir_path / update_file_path.name

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        # if not self._match(update_file_path=update_file_path):
        #     return

        if self._need_task_run_ins(update_file_path=update_file_path):
            # self.run(update_file_path=update_file_path)
            shutil.copy(
                src=update_file_path.as_posix(),
                dst=self.dst_file_path(update_file_path=update_file_path)
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CopyTask):
            return NotImplemented
        return (
            self.task_type == other.task_type
            and self._dest_dir_path == other._dest_dir_path
            and self._dst_suffixes == other._dst_suffixes
        )

    def __hash__(self) -> int:
        # list が入ると unhashable になるため tuple 化してから hash する
        dst_suffixes = tuple(self._dst_suffixes) if self._dst_suffixes is not None else tuple()
        src_suffixes = tuple(self._src_suffixes) if self._src_suffixes is not None else tuple()

        return hash(
            (
                self.task_type,
                self._src_dir_path,
                self._dest_dir_path,
                src_suffixes,
                dst_suffixes,
            )
        )


class CopyTaskStruct(CopyTask):
    def __init__(
            self,
            # task_type: TaskType,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            diff_sec: int = 10,
            wait_sec: int = 2,
            src_suffixes: Sequence[str] = [""],
            # dst_suffixes: Sequence[str] = [""]
            # observer:EventHandler=FileSystemEventHandler
    ):
        super().__init__(
            src_dir_path=src_dir_path,
            dst_dir_path=dst_dir_path,
            diff_sec=diff_sec,
            wait_sec=wait_sec,
            src_suffixes=src_suffixes,
            # observer:EventHandler=FileSystemEventHandler
        )

    @cached_classproperty
    def target_src_suffixes(cls) -> Sequence[str]:
        return []

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.copy

    """監視下で.bibの様に変更があればcopyする処理をするクラス"""

    @override
    def dst_file_path(self, update_file_path: Path) -> Path:
        if self._dest_dir_path.suffix:
            return self._dest_dir_path
        return self._dest_dir_path / update_file_path.name

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        # if not self._match(update_file_path=update_file_path):
        #     return

        if self._need_task_run_ins(update_file_path=update_file_path):
            # self.run(update_file_path=update_file_path)
            shutil.copy(src=update_file_path.as_posix(), dst=self.dst_file_path(update_file_path=update_file_path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CopyTask):
            return NotImplemented
        return (
            self.task_type == other.task_type
            and self._dest_dir_path == other._dest_dir_path
            and self._dst_suffixes == other._dst_suffixes
        )

    def __hash__(self) -> int:
        # list が入ると unhashable になるため tuple 化してから hash する
        dst_suffixes = tuple(self._dst_suffixes) if self._dst_suffixes is not None else tuple()
        src_suffixes = tuple(self._src_suffixes) if self._src_suffixes is not None else tuple()

        return hash(
            (
                self.task_type,
                self._src_dir_path,
                self._dest_dir_path,
                src_suffixes,
                dst_suffixes,
            )
        )
