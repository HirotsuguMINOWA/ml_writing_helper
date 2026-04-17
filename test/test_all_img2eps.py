"""
本アプリケーション(src/ml_writing_helper/main.py)の実行をテストする
- 挙動に関しては同フォルダのReadme.mdを必ず参照して下さい。変更も反映して下さい。
Abstract:
- 2つのスレッドを起動する、メインスレッドは、メインコード(src/ml_writing_helper/main.py)の実行。
- 2つ目のスレッドは、main.pyのテストを実施するための処理を行う。
- 2つの目のスレッドの処理内容
--- main.pyのスレッドと同時に起動して、10sec程sleep
--- exampleフォルダにあるpng/jpeg画像をfig_srcにcopyする。コピーしたらfig_genに.epsファイルへ変換されたファイルが生成される。その処理完了をassert確認せよ
--- exampleフォルダにある.pptxファイルをfig_srcにコピーする。コピーしたらfig_genにそのpowerpointファイル名.epsファイル名に変換されたファイルが生成される。その処理完了をassert確認せよ。
--- exampleフォルダにある.bibファイルをbib_srcフォルダにコピーする。コピーしたらbib_dstに先のbibファイルがコピーされる。その処理の完了をassertする
--- スレッド2の処理が終わったら、mainスレッドも停止させる。
"""

import shutil
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# sys.path.append("../ml_writing_helper")
from src.ml_writing_helper.main import Monitor, StateMonitor
from loguru import logger

# --- 設定定数 ---
WAIT_FOR_CONVERSION_SEC = 60  # 変換完了待機タイムアウト(秒)
POLL_INTERVAL_SEC = 1.0  # ポーリング間隔(秒)
STARTUP_SLEEP_SEC = 10  # Monitor起動待ちsleep時間(秒)

target_dir_p: Path = Path(__file__).parent.joinpath("tmp_conv")
# if not target_dir_p.exists():
target_dir_p.mkdir(exist_ok=True)

# --- フォルダ設定 ---
FIG_SAMPLE = Path(__file__).parent.joinpath("fig_sample")
if not FIG_SAMPLE.exists():
    raise FileNotFoundError(f"{FIG_SAMPLE=}が存在しない、指定誤り、直せ")
FIG_SRC = Path(f"{target_dir_p}/fig_src")
FIG_GEN = Path(f"{target_dir_p}/fig_gen")
BIB_SAMPLE = Path(f"{target_dir_p}/bib_sample")
BIB_SRC = Path(f"{target_dir_p}/bib_src")
BIB_DST = Path(f"{target_dir_p}/bib_dst")

# 対象拡張子
IMG_EXTS = [".png", ".jpg", ".jpeg"]
PPTX_EXTS = [".pptx"]
BIB_EXTS = [".bib"]


class AutoTester:
    """
    main.pyのMonitor処理を自動テストするクラス。

    スレッド1: Monitor（監視ループ）を起動・維持
    スレッド2: テストシナリオを順に実行し、完了後にMonitorを停止
    """

    def __init__(self):
        # self._monitor: Monitor | None = None
        self._monitor: Monitor = Monitor()
        self._monitor_ready = threading.Event()  # Monitor起動完了を通知するイベント
        self._stop_event = threading.Event()  # Monitor停止をリクエストするイベント

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    @staticmethod
    def init_dirs(*dirs: Path):
        """指定ディレクトリ内のファイルをすべて削除し、ディレクトリが無ければ作成する"""
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            for f in d.glob("**/*"):
                if f.is_file():
                    f.unlink()
            logger.info(f"Initialized dir: {d}")

    @staticmethod
    def copy_files(src_dir: Path, dst_dir: Path, exts: list[str]) -> list[Path]:
        """
        src_dir内の指定拡張子ファイルをdst_dirにコピーし、コピーしたファイルのリストを返す。
        """
        copied: list[Path] = []
        for ext in exts:
            for f in src_dir.glob(f"*{ext}"):
                shutil.copy(f, dst_dir)
                logger.info(f"Copied: {f} -> {dst_dir}")
                copied.append(dst_dir / f.name)
        return copied

    @staticmethod
    def wait_for_files(
            expected_files: list[Path],
            timeout: int = WAIT_FOR_CONVERSION_SEC,
            poll: float = POLL_INTERVAL_SEC) -> bool:
        """
        expected_filesが全て存在するまで待機する。
        timeout秒以内に揃えばTrue、タイムアウトでFalseを返す。
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if all(f.exists() for f in expected_files):
                return True
            time.sleep(poll)
        return False

    # ------------------------------------------------------------------
    # スレッド1: Monitor起動
    # ------------------------------------------------------------------

    def thread1_run_monitor(
            self,
            fig_src: Path, fig_gen: Path,
            bib_src: Path, bib_dst: Path,
            to_fmt: str):
        logger.info("[Thread1] Monitor 起動開始")

        # self._monitor.set_monitor(src_dir=fig_src, dst_dir=fig_gen, to_fmt=to_fmt)
        self._monitor.set_img_conv(src_dir=fig_src, dst_dir=fig_gen, to_fmt=to_fmt)
        # ★ bib はコピーのみ（変換なし）→ to_fmt=".bib" でそのまま渡す
        self._monitor.set_copy_task(src_dir=bib_src, dst_dir=bib_dst, src_suffixes=["bib"])

        # start_monitors()の前に必ずsetする（ブロッキング前に通知）
        self._monitor_ready.set()
        logger.info("[Thread1] Monitor 起動完了 - 監視ループ開始...")

        self._monitor.start_monitors()  # ここでブロック → Thread2はすでに動いている

        logger.info("[Thread1] Monitor 終了")

    # ------------------------------------------------------------------
    # スレッド2: テストシナリオ実行
    # ------------------------------------------------------------------

    def thread2_test_scenario(
            self,
            fig_sample: Path,
            fig_src: Path,
            fig_gen: Path,
            bib_sample: Path,
            bib_src: Path,
            bib_dst: Path,
            to_fmt: str):
        """
        テストシナリオをステップごとに実行する。
        """
        logger.info("[Thread2] テストスレッド 開始")

        # --- (1) Monitor起動を10秒待つ ---
        logger.info(f"[Thread2] Monitor起動待ち ({STARTUP_SLEEP_SEC}sec sleep)...")
        self._monitor_ready.wait()  # Thread1がreadyをセットするまで待機
        time.sleep(STARTUP_SLEEP_SEC)
        logger.info("[Thread2] 待機完了 - テスト開始")

        all_passed = True

        # ------------------------------------------------------------------
        # ステップ1: png/jpeg → fig_gen に .eps 変換確認
        # ------------------------------------------------------------------
        logger.info("[Thread2] === Step1: png/jpeg の変換テスト ===")
        copied_imgs = self.copy_files(fig_sample, fig_src, IMG_EXTS)
        if copied_imgs:
            expected_eps = [fig_gen / (f.stem + to_fmt) for f in copied_imgs]
            logger.info(f"[Thread2] 変換完了を待機中: {expected_eps}")
            ok = self.wait_for_files(expected_eps)
            try:
                assert ok, f"[FAIL] Step1: 変換タイムアウト。生成されなかったファイル: {[f for f in expected_eps if not f.exists()]}"
                logger.info("[Thread2] Step1: PASS ✅ png/jpeg → .eps 変換確認")
            except AssertionError as e:
                logger.error(e)
                all_passed = False
        else:
            logger.warning("[Thread2] Step1: fig_sampleにpng/jpegが見つかりません。スキップ")

        # ------------------------------------------------------------------
        # ステップ2: .pptx → fig_gen に .eps 変換確認
        # ------------------------------------------------------------------
        logger.info("[Thread2] === Step2: .pptx の変換テスト ===")
        copied_pptx = self.copy_files(fig_sample, fig_src, PPTX_EXTS)
        if copied_pptx:
            expected_pptx_eps = [fig_gen / (f.stem + to_fmt) for f in copied_pptx]
            logger.info(f"[Thread2] 変換完了を待機中: {expected_pptx_eps}")
            ok = self.wait_for_files(expected_pptx_eps)
            try:
                assert ok, f"[FAIL] Step2: 変換タイムアウト。生成されなかったファイル: {[f for f in expected_pptx_eps if not f.exists()]}"
                logger.info("[Thread2] Step2: PASS ✅ .pptx → .eps 変換確認")
            except AssertionError as e:
                logger.error(e)
                all_passed = False
        else:
            logger.warning("[Thread2] Step2: fig_sampleに.pptxが見つかりません。スキップ")

        # ------------------------------------------------------------------
        # ステップ3: .bib → bib_dst にコピー確認
        # ------------------------------------------------------------------
        logger.info("[Thread2] === Step3: .bib のコピーテスト ===")
        copied_bib = self.copy_files(bib_sample, bib_src, BIB_EXTS)
        if copied_bib:
            expected_bib_dst = [bib_dst / f.name for f in copied_bib]
            logger.info(f"[Thread2] bib_dstへのコピー完了を待機中: {expected_bib_dst}")
            ok = self.wait_for_files(expected_bib_dst)
            try:
                assert ok, f"[FAIL] Step3: bibコピータイムアウト。コピーされなかったファイル: {[f for f in expected_bib_dst if not f.exists()]}"
                logger.info("[Thread2] Step3: PASS ✅ .bib → bib_dst コピー確認")
            except AssertionError as e:
                logger.error(e)
                all_passed = False
        else:
            logger.warning("[Thread2] Step3: bib_sampleに.bibが見つかりません。スキップ")

        # ------------------------------------------------------------------
        # 全テスト完了 → Monitor(スレッド1)を停止
        # ------------------------------------------------------------------
        logger.info(f"[Thread2] 全テスト完了: {'全PASS ✅' if all_passed else '一部FAIL ❌'}")
        logger.info("[Thread2] Monitor停止をリクエスト...")
        if self._monitor is not None:
            self._monitor.stop()  # MonitorクラスのstopメソッドでThread1のループを終了させる
        logger.info("[Thread2] テストスレッド 終了")

    # ------------------------------------------------------------------
    # エントリポイント
    # ------------------------------------------------------------------

    def run(
            self,
            fig_sample: Path = FIG_SAMPLE,
            fig_src: Path = FIG_SRC,
            fig_gen: Path = FIG_GEN,
            bib_sample: Path = BIB_SAMPLE,
            bib_src: Path = BIB_SRC,
            bib_dst: Path = BIB_DST,
            to_fmt: str = "eps"):

        logger.info("=== AutoTester 開始 ===")

        # ディレクトリ初期化
        self.init_dirs(fig_src, fig_gen, bib_src, bib_dst)

        # ★ Thread1はdaemonスレッドとして直接起動（ThreadPoolExecutorから切り離す）
        t1 = threading.Thread(
            target=self.thread1_run_monitor,
            args=(fig_src, fig_gen, bib_src, bib_dst, to_fmt),
            name="Thread1-Monitor",
            daemon=True,  # メインプロセス終了時に自動終了
        )
        t1.start()
        logger.info("[Main] Thread1(Monitor) 起動")

        # ★ Thread2もdaemonスレッドとして直接起動
        t2 = threading.Thread(
            target=self.thread2_test_scenario,
            args=(fig_sample, fig_src, fig_gen, bib_sample, bib_src, bib_dst, to_fmt),
            name="Thread2-Tester",
            daemon=True,
        )
        t2.start()
        logger.info("[Main] Thread2(Tester) 起動")

        # ★ Thread2の完了をメインスレッドで待機（Thread1はMonitor.stop()で終了）
        t2.join()
        logger.info("[Main] Thread2 完了")

        # Thread1の終了を最大10秒待つ
        t1.join(timeout=10)
        if t1.is_alive():
            logger.warning("[Main] Thread1がタイムアウト後も生存中（daemonなので強制終了）")

        logger.info("=== AutoTester 完了 ===")


if __name__ == "__main__":
    tester = AutoTester()
    tester.run(to_fmt="eps")
