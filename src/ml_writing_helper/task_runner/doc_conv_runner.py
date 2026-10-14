"""
Markdown/HTML を PDF/HTML/DOCX へ変換する監視Task（doc_conv）
"""
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Final, override

from loguru import logger
from typed_classproperties import cached_classproperty
from watchdog.events import DirMovedEvent, FileMovedEvent

from ml_writing_helper.converter.doc_converter import (
    DEFAULT_DOC_ENGINE,
    DEFAULT_DOC_OUTPUT_FORMATS,
    SUPPORTED_INPUT_SUFFIXES,
    DocConverter,
)
from ml_writing_helper.enum_cls import TaskType
from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner

# 起動時の走査で中に入らないフォルダ（"." で始まるフォルダも入らない）
_SKIP_DIR_NAMES: Final[frozenset[str]] = frozenset({"node_modules", "__pycache__"})


class DocConvTask(ABCTaskRunner):
    """監視下の .md/.html が変更されたら PDF/HTML/DOCX へ変換する。src のフォルダ構成を dst に再現する。"""

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(src_dir_path:{self._src_dir_path}, dst_dir_path={self._dest_dir_path}, "
            f"formats={self._converter.output_formats}, engine={self._converter.engine})"
        )

    def __init__(
            self,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            output_formats: Sequence[str] = DEFAULT_DOC_OUTPUT_FORMATS,
            engine: str = DEFAULT_DOC_ENGINE,
            input_patterns: Sequence[str] | None = None,
            header_files: Sequence[str | Path] = (),
            marp_header_files: Sequence[str | Path] = (),
            copy_exts: Sequence[str] = (),
            diff_sec: int = 10,
            wait_sec: int = 2,
    ):
        super().__init__(
            src_dir_path=src_dir_path,
            dst_dir_path=dst_dir_path,
            diff_sec=diff_sec,
            wait_sec=wait_sec,
            src_suffixes=[s[1:] for s in SUPPORTED_INPUT_SUFFIXES],
            dst_suffixes=tuple(output_formats),
        )
        self._converter: Final[DocConverter] = DocConverter(
            src_root=self._src_dir_path,
            dst_root=self._dest_dir_path,
            output_formats=output_formats,
            engine=engine,
            input_patterns=input_patterns,
            header_files=header_files,
            marp_header_files=marp_header_files,
        )
        self._copy_exts: Final[tuple[str, ...]] = tuple(e.lower().lstrip(".") for e in copy_exts)

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.doc_conv

    @property
    def converter(self) -> DocConverter:
        return self._converter

    def _is_ignored(self, path: Path) -> bool:
        """一時ファイル・隠しファイルと、src の中にある dst フォルダ（出力先）を対象外にする。"""
        if path.name.startswith(("~", ".")) or path.stem.endswith("~"):
            return True
        src, dst = self._src_dir_path.resolve(), self._dest_dir_path.resolve()
        resolved = path.resolve()
        return dst != src and dst.is_relative_to(src) and resolved.is_relative_to(dst)

    def _is_copy_target(self, path: Path) -> bool:
        return path.suffix.lower().lstrip(".") in self._copy_exts

    def _outdated(self, src: Path, dst: Path, diff_sec: float) -> bool:
        if not dst.exists():
            return True
        return src.stat().st_mtime - dst.stat().st_mtime > diff_sec

    @override
    def run(self, update_file_path: Path, startup: bool = False) -> None:
        """変換（またはコピー）が必要なら実行する。

        起動時は src が出力より diff_sec 秒を超えて新しいときだけ、監視中は src が出力より新しければ実行する。
        """
        path = Path(update_file_path)
        if not path.is_file() or self._is_ignored(path):
            return
        diff_sec = self._diff_sec if startup else 0
        try:
            if self._converter.is_input_file(path):
                outputs = [d for d in self._converter.dst_paths(path) if d.resolve() != path.resolve()]
                if not any(self._outdated(path, d, diff_sec) for d in outputs):
                    logger.debug(f"Up-to-date: {path}")
                    return
                logger.info(f"文書変換: {path} → {', '.join(d.as_posix() for d in outputs)}")
                _ = self._converter.convert(path)
            elif self._is_copy_target(path):
                dst = self.dst_file_path(update_file_path=path)
                if dst.resolve() == path.resolve() or not self._outdated(path, dst, diff_sec):
                    return
                dst.parent.mkdir(parents=True, exist_ok=True)
                _ = shutil.copy2(path, dst)
                logger.info(f"[copy] {path} -> {dst}")
        except Exception as e:
            logger.exception(e)

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        self.run(update_file_path)

    @override
    def run_all_target_files_in_target_dir(self) -> None:
        """src 以下（サブフォルダを含む）の全ての対象ファイルを、必要なら変換する。"""
        for path in sorted(self._iter_files(self._src_dir_path)):
            self.run(path, startup=True)

    def _iter_files(self, folder: Path):
        try:
            entries = list(folder.iterdir())
        except OSError as e:
            logger.warning(f"Cannot read folder {folder}: {e}")
            return
        for p in entries:
            if p.is_dir():
                if p.name.startswith(".") or p.name in _SKIP_DIR_NAMES or self._is_ignored(p):
                    continue
                yield from self._iter_files(p)
            elif p.is_file():
                yield p

    @override
    def on_moved(self, event: FileMovedEvent | DirMovedEvent) -> None:
        # エディタの「一時ファイルに書いてリネーム」保存では、移動先が変更後のファイル
        if event.is_directory or isinstance(event.dest_path, bytes):
            return
        logger.info(f"Moved : {Path(event.dest_path).name}")
        self.run(Path(event.dest_path))

    @override
    def dst_file_path(self, update_file_path: Path) -> Path:
        """先頭の出力形式での出力先（コピー対象ならコピー先）"""
        if self._is_copy_target(update_file_path):
            return self._converter.dst_path(update_file_path)
        return self._converter.dst_path(update_file_path, self._converter.output_formats[0])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DocConvTask):
            return NotImplemented
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        c = self._converter
        return hash(
            (
                self.task_type,
                self._src_dir_path,
                self._dest_dir_path,
                c.output_formats,
                c.engine,
                tuple(p.pattern for p in c.input_patterns),
                c.header_files,
                c.marp_header_files,
                self._copy_exts,
            )
        )
