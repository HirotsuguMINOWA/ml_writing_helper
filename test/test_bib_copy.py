from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path

from loguru import logger
from src.ml_writing_helper.main import Monitor

WAIT_TIMEOUT_SEC = 30
POLL_INTERVAL_SEC = 0.5
STARTUP_SLEEP_SEC = 2

BASE_DIR = Path(__file__).parent
TMP_DIR = BASE_DIR / "tmp_conv"

FIG_SAMPLE = BASE_DIR / "fig_sample"
SRC_BIB_FILE = FIG_SAMPLE / "test_bib.bib"

BIB_SRC = TMP_DIR / "bib_src"
BIB_DST = TMP_DIR / "bib_dst"


def _init_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        for p in d.glob("**/*"):
            if p.is_file():
                p.unlink()


def _wait_for_file(path: Path, timeout: int = WAIT_TIMEOUT_SEC, poll: float = POLL_INTERVAL_SEC) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return True
        time.sleep(poll)
    return False


def test_bib_copy() -> None:
    """
    bib_src を監視し、fig_sample/test_bib.bib を bib_src にコピーしたら
    bib_dst に同名ファイルがコピーされることを確認する。
    """
    assert FIG_SAMPLE.exists(), f"fig_sample が存在しません: {FIG_SAMPLE}"
    assert SRC_BIB_FILE.exists(), f"入力 bib が存在しません: {SRC_BIB_FILE}"

    _init_dirs(BIB_SRC, BIB_DST)

    monitor = Monitor()
    ready = threading.Event()

    def _run_monitor() -> None:
        logger.info("[Thread1] monitor start")
        # ReadMe / 既存テスト方針に合わせて copy タスクを設定
        monitor.set_copy_task(src_dir=BIB_SRC, dst_dir=BIB_DST, src_suffixes=["bib"])
        ready.set()
        monitor.start_monitors()  # blocking
        logger.info("[Thread1] monitor stopped")

    t = threading.Thread(target=_run_monitor, name="bib-copy-monitor", daemon=True)
    t.start()

    # monitor 起動待ち
    ready.wait(timeout=10)
    time.sleep(STARTUP_SLEEP_SEC)

    # fig_sample/test_bib.bib -> bib_src
    copied_src = BIB_SRC / SRC_BIB_FILE.name
    shutil.copy(SRC_BIB_FILE, copied_src)
    logger.info(f"copied: {SRC_BIB_FILE} -> {copied_src}")

    expected_dst = BIB_DST / SRC_BIB_FILE.name
    ok = _wait_for_file(expected_dst)

    # 終了処理
    monitor.stop()
    t.join(timeout=5)

    assert ok, f"bib コピーに失敗: {expected_dst} が作成されませんでした"
    logger.success(f"PASS: {expected_dst} が作成されました")


if __name__ == "__main__":
    test_bib_copy()