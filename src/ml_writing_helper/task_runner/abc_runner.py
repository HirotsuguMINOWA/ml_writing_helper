import os
import platform
import time
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Final, override, Callable, Self
from loguru import logger
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler, FileSystemEvent, DirMovedEvent, FileMovedEvent
# from watchdog.observers import BaseObserver
# from watchdog.observers.fsevents import FSEventsObserver
# from watchdog.observers.inotify import InotifyObserver
# from watchdog.observers.kqueue import KqueueObserver
# from watchdog.observers.polling import PollingObserver
# from watchdog.observers.read_directory_changes import WindowsApiObserver

from src.ml_writing_helper.enum_cls import TaskType, StateMonitor
from typed_classproperties import cached_classproperty


@dataclass
class ABCTaskRunner(ABC, FileSystemEventHandler):
    """監視TaskのTOPクラス"""
    __slots__ = ["_src_suffixes", "_dst_suffixes", "_wait_sec", "_directory_path", "_dest_dir_path", "_diff_sec"]

    def __init__(
            self,
            # task_type: TaskType,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            diff_sec: int = 10,
            wait_sec: int = 2,
            src_suffixes: Sequence[str] = [""],
            dst_suffixes: Sequence[str] = [""]
            # observer:EventHandler=FileSystemEventHandler
    ):
        # FileSystemEvent.__init__(self)
        # TODO: check拡張子
        # self._task_type: Final[TaskType] = task_type
        # self._src_dir_path: Final[Path] = Path(src_dir_path)
        self._src_suffixes = src_suffixes
        self._dst_suffixes = dst_suffixes
        self._wait_sec = wait_sec
        self._src_dir_path: Final[Path] = Path(src_dir_path)
        self._dest_dir_path: Final[Path] = Path(dst_dir_path)
        # self._target_exts: Final[Sequence[str]] = target_exts
        self._diff_sec: Final[int] = diff_sec

    def set_observer(
            self,
            observer,
            sleep_sec: int | float = 1,
            observer_backend: str | None = None
    ) -> None:
        """
        Start monitoring change on FS according to set
        : param sleep_sec:
        : return:
        """
        try:
            # event_handler = self

            # ** ObserverをCLIパラで指定可能
            # backend = (
            #     self._observer_backend
            #     if observer_backend is None
            #     else _normalize_observer_backend(observer_backend)
            # )
            # observer = _build_observer(backend)
            # logger.info(f"Using watchdog observer backend: {backend}")
            # for self.src_dir_path, self.dest_dir_path in self._monitors.keys():

            # ** Check src path
            if not self.src_dir_path.exists():
                raise Exception("[Error] The path was not exists: %s" % self.src_dir_path)
            logger.info("Set monitoring Path:%s" % self.src_dir_path)

            # ** Check base_self.dest_dir_path path
            if not self._dest_dir_path.exists():
                logger.info("右記PATH存在しません、作成しますか?:%s" % self._dest_dir_path)

                res = ""
                while res not in ("y", "n", "Y", "N"):
                    res = input("make dir?(y/n)")
                if res in ("y", "Y"):
                    self._dest_dir_path.mkdir(parents=True, exist_ok=True)
                else:
                    raise Exception("[Error] dst_pathが存在しないので終了しました")
            logger.info("Set exporting Path:%s" % self._dest_dir_path)

            # ! set into scheduling
            # !
            observer.schedule(self, self.src_dir_path.as_posix(), recursive=True)

            # ! タイムスタンプ確認: srcがdstより5秒以上新しければコピー
            # to_fmt_in = self._monitor_fmts.get((self.src_dir_path, self.dest_dir_path), "")
            # moniko = self._monitors[self.src_dir_path, self.dest_dir_path]
            # for src_file in self.src_dir_path.rglob("*"):
            #     if not src_file.is_file():
            #         continue
            #     dst_file = self.dest_dir_path / (src_file.stem + to_fmt_in)
            #     src_mtime = src_file.stat().st_mtime
            #     if not dst_file.exists() or src_mtime - dst_file.stat().st_mtime >= 5:
            #         logger.info(f"[Startup] タイムスタンプ差>=5秒: {src_file.name} -> コピー実行")
            #         moniko(src_file.as_posix())
        except Exception as e:
            logger.exception(e)
            raise Exception(e)

    @cached_classproperty
    @abstractmethod
    def task_type(cls) -> TaskType:
        raise NotImplementedError

    # @cached_classproperty
    # @abstractmethod
    @property
    def src_suffixes(self) -> Sequence[str]:
        # raise NotImplementedError
        return self._src_suffixes

    @property
    def dst_suffixes(self) -> Sequence[str]:
        # raise NotImplementedError
        return self._dst_suffixes

    @property
    def src_dir_path(self) -> Path:
        return self._src_dir_path

    # @src_dir_path.setter
    # def src_path(self, v: str | Path):
    #     self._src_path = Path(v)
    def run(self, update_file_path: Path) -> None:
        if self._src_suffixes is not None and update_file_path.suffix[1:] not in self._src_suffixes:
            logger.debug(f"拡張子{update_file_path.suffix}はコピー対処外")
            return None
        return self._run_internal(update_file_path=update_file_path)

    @abstractmethod
    def _run_internal(self, update_file_path: Path) -> None:
        raise NotImplementedError

    def run_all_target_files_in_target_dir(self) -> None:
        """ターゲットDirPath(SrcPath)内の全てのソース・ファイルに対してrunする。"""
        # if self.target_exts is None:
        #     return
        for ext in self._src_suffixes:
            file_lists = self.src_dir_path.glob(f"*{'' if ext == '' else f'.{ext}'}")
            for target_f_path in file_lists:
                self.run(update_file_path=target_f_path)

    def _match(self, update_file_path: Path) -> bool:
        """src_pathの変更が本Taskに該当するか否かを判定"""
        return (
                self._src_dir_path.as_posix() in update_file_path.parent.as_posix()
                and update_file_path.suffix in self._src_suffixes
        )

    @abstractmethod
    def dst_file_path(self, update_file_path: Path) -> Path:
        raise NotImplementedError

    # def _road_balancer(self, event: FileSystemEvent) -> None:
    #     """
    #
    #     :param event:
    #     :return:
    #     """
    #     if event.is_directory:
    #         return  # 監視対象ではない。
    #     # print(f"event.src_path:{self.is_nfd(event.src_path)},{event.src_path}")
    #     for (
    #             key_path,
    #             closure,
    #     ) in self._monitors.items():
    #         # print(f"key_path:{self.is_nfd(key_path[0].as_posix())},{event.src_path}")
    #         """ Check the env. applied NDF or not"""
    #         if platform.system() == "Darwin":
    #             """convert NDF to NFC """
    #             converted = unicodedata.normalize("NFC", key_path[0].as_posix())
    #             tmp_src_path = unicodedata.normalize("NFC", event.src_path)
    #         else:
    #             converted = key_path[0].as_posix()
    #             tmp_src_path = event.src_path
    #         # if converted in event.src_path:  # 0: src_path, 1:dst_path
    #         if converted in tmp_src_path:  # 0: src_path, 1:dst_path
    #             if event.event_type == "moved":
    #                 src_path = event.dest_path
    #             else:
    #                 src_path = event.src_path
    #             closure(src_path)  # run

    def event_common(
            self,
            event: FileSystemEvent,
            state_change: str,
            start: bool = True,
    ) -> None:
        if start:
            self._state = StateMonitor.convert
        filepath = event.src_path
        filename = os.path.basename(filepath)
        # print(self.msg_event_start)
        logger.info(f"{state_change} : {filename}")
        # cls.convert(src_file_apath=event.src_path, dst_dir_apath=cls._dst_pl, fmt_if_dst_without_ext=cls._to_fmt)  # , _to_fmt="png")
        if isinstance(event.src_path,bytes):
            logger.debug(f"{event.src_path=}はbytes型です。何もせずにTask skipします。")
            return None
        if start:
            # self._road_balancer(event=event)
            self.run(update_file_path=Path(event.src_path))
            self._state = StateMonitor.wait
        print("------------- End Event --------------------")

    # @property
    # def dest_file_path(self) -> Path:
    #     """生成先ファイルPATHを返す"""
    #     return self._dest_file_path()
    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory or isinstance(event.src_path, bytes):
            return
        time.sleep(self._wait_sec)  # 画像生成まで少し待つ
        self.event_common(event, state_change="Modified")
        # self.run(update_file_path=Path(event.src_path))

    # @override
    # def on_modified(self, event: FileSystemEvent) -> None:
    #     time.sleep(self._wait_sec)  # 画像生成まで少し待つ
    #     self.event_common(event, state_change="Modified")
    #     # filepath = event.src_path
    #     # filename = os.path.basename(filepath)
    #     # print(self.msg_event_start)
    #     # logger.info("Modified:%s" % filename)
    #     # self._road_balancer(event=event)

    @override
    def on_created(self, event: FileSystemEvent) -> None:
        """

        :param event:
        :return:
        """
        self.event_common(event, state_change="Created")
        # filepath = event.src_path
        # filename = os.path.basename(filepath)
        # print(self.msg_event_start)
        # logger.info("Created: %s" % filename)
        # # cls.convert(src_file_apath=event.src_path, dst_dir_apath=cls._dst_pl, fmt_if_dst_without_ext=cls._to_fmt)  # , _to_fmt="png")
        # self._road_balancer(event=event)

    @override
    def on_deleted(self, event: FileSystemEvent) -> None:
        self.event_common(event, state_change="Deleted", start=False)
        # filepath = event.src_path
        # filename = os.path.basename(filepath)
        # print("\n\n")
        # logger.info("Deleted:%s" % filename)
        # cls._road_balancer(event=event)

    @override
    def on_moved(self, event: FileMovedEvent | DirMovedEvent) -> None:
        """
        ファイル移動時のイベント
        - Medeneley変換では、event.dest_pathが移動後のPATHを示し、それを変換に使えないかと思う
        :param event:
        :type event: FileMovedEvent | DirMovedEvent
        :return:
        """
        self.event_common(event, state_change="Moved")
        # filepath = event.src_path
        # filename = os.path.basename(filepath)
        # print(self.msg_event_start)
        # logger.info("Moved:%s" % filename)
        # # cls.convert(src_file_apath=event.dest_path, dst_dir_apath=cls._dst_pl,fmt_if_dst_without_ext=cls._to_fmt)  # , _to_fmt="png")
        # self._road_balancer(event=event)

    def _need_task_run_ins(self, update_file_path: Path):
        return self.need_task_run_staticmethod(
            src_path=self._src_dir_path,
            dest_path=self.dst_file_path(update_file_path=update_file_path),
            diff_sec=self._diff_sec,
            # target_src_suffixes=self._src_suffixes
        )

    @staticmethod
    def need_task_run_staticmethod(
            dest_path: str | Path,
            src_path: str | Path,
            # target_src_suffixes:Sequence[str]|None,
            diff_sec: int = 10
    ) -> bool:
        """src_pathとdest_pathのファイルを比較して、タイムスタンプ差がdiff_sec以上ならsrc_pathをdest_pathへコピーする"""
        src = Path(src_path)
        dst = Path(dest_path)

        if not src.exists():
            raise FileNotFoundError(f"src_path does not exist: {src}")

        # dest_path がディレクトリなら同名ファイルとして扱う
        if dst.exists() and dst.is_dir():
            dst = dst / src.name

        # ** コピー先が存在しない場合はそのままコピー
        if not dst.exists():
            # dst.parent.mkdir(parents=True, exist_ok=True)
            # return shutil.copy2(src, dst)
            return True

        src_mtime = src.stat().st_mtime
        dst_mtime = dst.stat().st_mtime

        # ! srcとdstファイルのタイムスタンプの差がdiff_sec以内ならコピーしない
        if abs(src_mtime - dst_mtime) <= diff_sec:
            # dst.parent.mkdir(parents=True, exist_ok=True)
            # return shutil.copy2(src, dst)
            return False
        return True

    # @staticmethod
    # def move(src_path: str | Path, dest_path: str | Path):
    #     shutil.move(src=src_path, dst=dest_path)
    @abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError
