from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Final, override
from loguru import logger
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from src.ml_writing_helper.enum_cls import TaskType
from typed_classproperties import cached_classproperty


@dataclass
class ABCTaskRunner(ABC, FileSystemEventHandler):
    """監視TaskのTOPクラス"""

    def __init__(
        self,
        # task_type: TaskType,
        src_dir_path: str | Path,
        dest_dir_path: str | Path,
        # target_exts: Sequence[str],
        diff_sec: int = 10,
        # observer:EventHandler=FileSystemEventHandler
    ):
        super().__init__()
        # TODO: check拡張子
        # self._task_type: Final[TaskType] = task_type
        # self._src_dir_path: Final[Path] = Path(src_dir_path)
        self.directory_path: Final[Path] = Path(src_dir_path)
        self._dest_dir_path: Final[Path] = Path(dest_dir_path)
        # self._target_exts: Final[Sequence[str]] = target_exts
        self._diff_sec: Final[int] = diff_sec

    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory or isinstance(event.src_path, bytes):
            return
        self.run(update_file_path=Path(event.src_path))

    @cached_classproperty
    @abstractmethod
    def task_type(cls) -> TaskType:
        raise NotImplementedError

    @cached_classproperty
    @abstractmethod
    def target_src_exts(cls) -> Sequence[str]:
        raise NotImplementedError

    @property
    def src_dir_path(self) -> Path:
        return self.directory_path

    # @src_dir_path.setter
    # def src_path(self, v: str | Path):
    #     self._src_path = Path(v)
    @abstractmethod
    def run(self, update_file_path: Path) -> None:
        raise NotImplementedError

    def run_dir(self) -> None:
        # if self.target_exts is None:
        #     return
        for ext in self.target_src_exts:
            file_lists = self.src_dir_path.glob(f"*/*.{ext}")
            for target_f_path in file_lists:
                self.run(update_file_path=target_f_path)

    def _match(self, update_file_path: Path) -> bool:
        """src_pathの変更が本Taskに該当するか否かを判定"""
        return (
            self._src_dir_path.as_posix() in update_file_path.parent.as_posix()
            and update_file_path.suffix in self.target_src_exts
        )

    @abstractmethod
    def dest_file_path(self, update_file_path: Path) -> Path:
        raise NotImplementedError

    # @property
    # def dest_file_path(self) -> Path:
    #     """生成先ファイルPATHを返す"""
    #     return self._dest_file_path()

    def copy_in_timestamp_ins(self, update_file_path: Path):
        return self.copy_in_timestamp(
            src_path=self._src_dir_path,
            dest_path=self.dest_file_path(update_file_path=update_file_path),
            diff_sec=self._diff_sec,
        )

    @staticmethod
    def copy_in_timestamp(
        dest_path: str | Path, src_path: str | Path, diff_sec: int = 10
    ) -> str | Path:
        """src_pathとdest_pathのファイルを比較して、タイムスタンプ差がdiff_sec以上ならsrc_pathをdest_pathへコピーする"""
        src = Path(src_path)
        dst = Path(dest_path)

        if not src.exists():
            raise FileNotFoundError(f"src_path does not exist: {src}")

        # dest_path がディレクトリなら同名ファイルとして扱う
        if dst.exists() and dst.is_dir():
            dst = dst / src.name

        # コピー先が存在しない場合はそのままコピー
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            return shutil.copy2(src, dst)

        src_mtime = src.stat().st_mtime
        dst_mtime = dst.stat().st_mtime

        if abs(src_mtime - dst_mtime) >= diff_sec:
            dst.parent.mkdir(parents=True, exist_ok=True)
            return shutil.copy2(src, dst)

        return dst

    @staticmethod
    def move(src_path: str | Path, dest_path: str | Path):
        shutil.move(src=src_path, dst=dest_path)
