import os
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import override

from loguru import logger
from typed_classproperties import cached_classproperty

from ml_writing_helper.dst_sync import iter_src_files, prune_dst
from ml_writing_helper.enum_cls import TaskType
from ml_writing_helper.link_checker import check_links
from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner


class CopyTask(ABCTaskRunner):
    def __repr__(self):
        return f'{self.__class__.__name__}(src_dir_path:{self._src_dir_path}, dst_dir_path={self._dest_dir_path}, src_suffixes={self._src_suffixes})'

    def __init__(
            self,
            # task_type: TaskType,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            diff_sec: int = 10,
            wait_sec: int = 2,
            src_suffixes: Sequence[str] = [""],
            sync_dst: bool = False,
            check_link: bool = False,
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
        self._sync_dst = sync_dst
        self._check_link = check_link

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
        rel = Path(os.path.abspath(update_file_path)).relative_to(os.path.abspath(self._src_dir_path))
        return self._dest_dir_path / rel

    @override
    def run_all_target_files_in_target_dir(self) -> None:
        if self._dest_dir_path.suffix:
            return super().run_all_target_files_in_target_dir()
        src_files = list(iter_src_files(self._src_dir_path, exclude=self._dest_dir_path))
        if self._sync_dst:
            prune_dst(self._dest_dir_path, (self._dest_dir_path / p.relative_to(self._src_dir_path) for p in src_files))
        for src_file in src_files:
            self.run(update_file_path=src_file)

    @override
    def run(self, update_file_path: Path) -> None:
        # コピー対象の拡張子に関係なく、md/html のリンクを確認する
        if self._check_link:
            check_links(update_file_path)
        super().run(update_file_path=update_file_path)

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        dst_path = self.dst_file_path(update_file_path=update_file_path)
        if self._need_task_run_ins(update_file_path=update_file_path):
            # self.run(update_file_path=update_file_path)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                src=update_file_path.as_posix(),
                dst=dst_path
            )
            logger.debug(f"[Copy完了] src:{update_file_path.as_posix()} → {dst_path}")
        else:
            logger.warning(f"[!Copy非完了] src:{update_file_path.as_posix()} → {dst_path}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CopyTask):
            return NotImplemented
        return (
                self.task_type == other.task_type
                and self._dest_dir_path == other._dest_dir_path
                and self._dst_suffixes == other._dst_suffixes
                and self._sync_dst == other._sync_dst
                and self._check_link == other._check_link
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
                self._sync_dst,
                self._check_link,
            )
        )
