from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from src.ml_writing_helper.task_runner.copy_runner import CopyTask


def _make_runner(src_dir: Path, dst_dir: Path, diff_sec: int = 5) -> CopyTask:
    # src_suffixes は ABCTaskRunner.run() の実装上「拡張子(ドットなし)」で指定
    return CopyTask(
        src_dir_path=src_dir,
        dst_dir_path=dst_dir,
        diff_sec=diff_sec,
        src_suffixes=["bib"],
        # dst_suffixes=["bib"],
    )


def test_first_run_copy_bib_when_dst_not_exists(tmp_path: Path=Path(__file__).parent.joinpath("tmp_first_run")) -> None:
    """
    初回起動時: dst にファイルが無ければ src -> dst へコピーされること
    """
    if not tmp_path.exists():
        tmp_path.mkdir(parents=True, exist_ok=True)
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.mkdir(parents=True, exist_ok=True)

    sample_bib = Path(__file__).parent / "fig_sample" / "test_bib.bib"
    assert sample_bib.exists(), f"sample が存在しません: {sample_bib}"

    src_file = src_dir / sample_bib.name
    shutil.copy(sample_bib, src_file)

    runner = _make_runner(src_dir, dst_dir, diff_sec=5)
    runner.run_all_target_files_in_target_dir()

    dst_file = dst_dir / sample_bib.name
    assert dst_file.exists(), "dst に .bib がコピーされていません"
    assert dst_file.read_text(encoding="utf-8") == src_file.read_text(encoding="utf-8")


def test_first_run_copy_bib_when_dst_is_old(tmp_path: Path) -> None:
    """
    初回起動時: dst が古ければ（mtime差がdiff_sec超）src -> dst へ再コピーされること
    """
    src_dir = tmp_path / "bib_src"
    dst_dir = tmp_path / "bib_dst"
    src_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.mkdir(parents=True, exist_ok=True)

    sample_bib = Path(__file__).parent / "fig_sample" / "test_bib.bib"
    assert sample_bib.exists(), f"sample が存在しません: {sample_bib}"

    src_file = src_dir / sample_bib
    shutil.copy(sample_bib, src_file)

    dst_file = dst_dir / sample_bib.name
    dst_file.write_text("old-content", encoding="utf-8")

    # dst を十分古くする（差分 > diff_sec）
    now = time.time()
    os.utime(src_file, (now, now))
    old_time = now - 120
    os.utime(dst_file, (old_time, old_time))

    before_mtime = dst_file.stat().st_mtime

    runner = _make_runner(src_dir, dst_dir, diff_sec=5)
    runner.run_all_target_files_in_target_dir()

    assert dst_file.exists(), "dst ファイルが消失しています"
    assert dst_file.read_text(encoding="utf-8") == src_file.read_text(encoding="utf-8")
    assert dst_file.stat().st_mtime != before_mtime, "古い dst が更新されていません"