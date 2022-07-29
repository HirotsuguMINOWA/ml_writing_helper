"""
- FIXME: 停止は、変換が終わった事を目視で確認し、手動で停止させる事が必要
"""
# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
# and need set working dir at prj root(src)
import queue
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

sys.path.append("../ml_writing_helper")
from ml_writing_helper.main import Monitor, StateMonitor
from loguru import logger


class AutoTester:
    _monitor: Monitor = None

    def __init__(self):
        self._standby_monitoring = False

    @classmethod
    def start(cls, sample="fig_sample", src="fig_src", dst="fig_gen", to_fmt=".eps", target_exts=[], excludes=[]):
        """

        :param sample:
        :param src:
        :param dst:
        :param to_fmt:
        :param target_exts: 変換対象の拡張子
        :param excludes:
        :return:
        """
        cls.main(sample=Path(sample), src=Path(src), dst=Path(dst), to_fmt=to_fmt, target_exts=target_exts,
                 excludes=excludes)

    @classmethod
    def start_monitoring(cls, src, dst, to_fmt):
        print("Start start_monitoring: Start Monitoring dirs")
        cls._monitor = Monitor()
        cls._monitor.set_monitor(
            src_dir=src
            , dst_dir=dst
            , to_fmt=to_fmt
        )
        cls._standby_monitoring = True
        print("スタンバイ monitoring")
        cls._monitor.start_monitors()
        print("End start_monitoring")

    @classmethod
    def pattener(cls, target_ext: List[str]) -> str:
        """
        .globメソッドを使って、複数の拡張子指定したファイルの抽出用パターンの生成
        :param target_ext:
        :return:
        """
        pattern = "("
        for i, ext in enumerate(target_ext):
            if i == 0:
                pattern += ext
            else:
                pattern += '|' + ext
        pattern += ")"
        return pattern

    @classmethod
    def task_copy_src_files(cls, smpl: Path, src: Path,
                            target_ext: List[str],
                            excludes: List[str] = None,
                            sleep_sec: int = 10):
        """Copy sample dir's file to src dir"""

        msg = "Copy Task"
        print("Start " + msg)
        while not cls._standby_monitoring:
            time.sleep(1)
        # 　monitorに投げるファイルPATHの抽出
        if len(target_ext) > 0:
            """Exportするextをえらぶ"""
            pattern = cls.pattener(target_ext)
            # print("pattern: " + pattern)
            # print("files_tmp", list(smpl.glob('*')))
            files = [p for p in smpl.glob('*') if re.search('.' + pattern, str(p))]
        else:
            files = smpl.glob('**/*')
        files = list(files)
        print(f"files to copy: {files}")
        for fn in files:
            if excludes is None or len(excludes) == 0 or fn.suffix not in excludes:
                print("copy %s to %s" % (fn.resolve().as_posix(), src.resolve().as_posix()))
                shutil.copy(fn, src.as_posix())
        cls._complete_copy = True
        logger.info(f"End of Copy: {msg}")
        # MEMO: ここでexit(0)しても、このスレッドが終わるだけで、別スレッドが終わらない。         # logger.info(f"Exit after Sleep({sleep_sec}sec)")
        # time.sleep(sleep_sec)
        # exit(0)

    # @staticmethod
    # def copy(a_file: Path, src: Path, excludes):
    #     if a_file.suffix not in excludes:
    #         print(f"copy {a_file} to {src}")
    #         shutil.copy(a_file, src)

    @staticmethod
    def init_dirs(src, dst):
        """
        次のdirのファイルを削除
        - fig_src
        - generated files
        :param src:
        :param dst:
        :return:
        """
        msg = "Task2: Copy files to src dir"
        logger.info(f"start: {msg}")
        # src,dst dir内のfiles削除

        for a_path in (src, dst):
            logger.info(f"Init: {a_path}")
            p_tmp = Path(a_path)
            files = p_tmp.glob('**/*')
            for a_file in files:
                a_file.unlink(missing_ok=False)
            # if os.path.exists(a_path):
            #     shutil.rmtree(a_path)
            # os.mkdir(a_path)
        logger.info("cp1 task_copy_src_files")

    @classmethod
    def main(cls, sample: Path, src: Path, dst: Path, to_fmt: str, target_exts: List[str] = [],
             excludes: List[str] = [], maxsize: int = 10):
        logger.info("Test Main: start")
        cls.init_dirs(src, dst)
        # files = sample.glob("*")
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="thread") as executor:
            e_task1 = executor.submit(cls.start_monitoring, src, dst, to_fmt)
            e_task2 = executor.submit(cls.task_copy_src_files, sample, src, target_exts, excludes)
            #
            states = queue.Queue(maxsize=maxsize)
            # time.sleep(2)
            while True:
                time.sleep(0.5)
                """Taskが終了しようという仕組み。ただし、今は機能していない"""
                if len(states.queue) >= maxsize and all(states.queue) and e_task2.done():
                    # print("Enter break")
                    e_task1.cancel()
                    break
                if len(states.queue) >= maxsize:
                    states.get_nowait()
                if cls._monitor.state == StateMonitor.wait:
                    # states.pop()
                    # print("branch2")
                    states.put(True)
                    time.sleep(1)
                else:
                    # states.pop()
                    # print("branch3")
                    states.put(False)
                # print("state:", states.queue)
                # print("flag:", cls._complete_copy)

                # if i > 5000:

            logger.info("Test Main: End")
            exit(0)  # スレッドを強制終了
            # exit(0)


if __name__ == "__main__":
    # AutoTester.start(target_exts=[".png"])
    AutoTester.start(to_fmt=".eps", target_exts=[])
