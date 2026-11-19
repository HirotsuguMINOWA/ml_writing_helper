"""--sync-dst: dst のフォルダ構成を src と揃え、src に対応するものが無い dst のファイルを削除する"""

import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Final

from loguru import logger

_SKIP_DIR_NAMES: Final[frozenset[str]] = frozenset({"node_modules", "__pycache__"})


def sync_dst_problem(src: Path, dst: Path) -> str | None:
    """sync_dst を安全に使えない src / dst の組み合わせなら理由を返す（問題なしなら None）。"""
    s, d = src.resolve(), dst.resolve()
    if d == s:
        return "sync_dst（--sync-dst）を使うには「dst」を「src」と別のフォルダにしてください（同じだと src のファイルを削除してしまいます）"
    if s.is_relative_to(d):
        return "sync_dst（--sync-dst）では「src」を「dst」の中に置けません（dst の整理で src のファイルを削除してしまいます）"
    if dst.exists() and not dst.is_dir():
        return "sync_dst（--sync-dst）では「dst」にフォルダを指定してください（ファイルは指定できません）"
    return None


def iter_src_files(src: Path, exclude: Path | None = None) -> Iterator[Path]:
    """src 以下（サブフォルダを含む）の全ファイル。隠しファイル・node_modules・__pycache__・exclude（出力先）は除く。"""
    yield from _iter_files(src, exclude.resolve() if exclude is not None else None)


def _iter_files(folder: Path, excluded: Path | None) -> Iterator[Path]:
    try:
        entries = sorted(folder.iterdir())
    except OSError as e:
        logger.warning(f"フォルダを読めませんでした: {folder} ({e})")
        return
    for p in entries:
        if p.name.startswith(".") or p.name in _SKIP_DIR_NAMES:
            continue
        if p.is_dir():
            if excluded is not None and p.resolve() == excluded:
                continue
            yield from _iter_files(p, excluded)
        elif p.is_file():
            yield p


def find_extra_dst_files(dst: Path, expected: Iterable[Path]) -> list[Path]:
    """dst 以下のファイルのうち expected に含まれないものを返す。"""
    if not dst.is_dir():
        return []
    keep = {p.resolve() for p in expected}
    return [path for path in _iter_files(dst, None) if path.resolve() not in keep]


def confirm_delete(extras: Sequence[Path], dst: Path) -> bool:
    """削除候補を表示して Y/N を確認する。対話できない（TTY でない）場合は削除せず False を返す。"""
    if not sys.stdin.isatty():
        logger.warning(f"[sync-dst] 対話できないため削除をスキップします（削除候補 {len(extras)} 件, dst: {dst}）")
        return False
    print(f"[sync-dst] src に対応しないファイルが {len(extras)} 件あります（dst: {dst}）:")
    for path in extras:
        print(f"  - {path.relative_to(dst).as_posix()}")
    try:
        answer = input("これらを削除しますか？ [y/N]: ")
    except EOFError:
        return False
    return answer.strip().lower() in ("y", "yes")


def _delete_files(dst: Path, files: Sequence[Path]) -> list[Path]:
    removed: list[Path] = []
    for path in files:
        try:
            path.unlink()
        except OSError as e:
            logger.error(f"[sync-dst] 削除できませんでした: {path} ({e})")
            continue
        logger.info(f"[sync-dst] 削除: {path}")
        removed.append(path)
        parent = path.parent
        while parent != dst and parent.is_relative_to(dst) and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    return removed


def prune_dst(dst: Path, expected: Iterable[Path]) -> list[Path]:
    """dst 以下で expected に含まれないファイルを確認のうえ削除し、空になったフォルダも削除する。削除したファイルを返す。"""
    extras = find_extra_dst_files(dst, expected)
    if not extras or not confirm_delete(extras, dst):
        return []
    return _delete_files(dst, extras)
