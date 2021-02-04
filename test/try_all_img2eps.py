# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
# and need set working dir at prj root(ml_writing_helper)
import re
import shutil
import sys
from pathlib import Path
# sys.path.append("/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/src")
from typing import List

sys.path.append("../src")
from main import Monitor, StateMonitor
import time
from concurrent.futures import ThreadPoolExecutor


# from logging import StreamHandler, Formatter, INFO, getLogger


class AutoTester:
    _monitor: Monitor = None

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
        # cls.to_fmt = to_fmt
        # cls.src = src
        # cls.sample = sample
        # cls.dst = dst
        #
        # cls.exc_ext = exe_ext
        #
        # cls.e_task1 = None
        cls._completed_copy = False
        cls.main(sample=Path(sample), src=Path(src), dst=Path(dst), to_fmt=to_fmt, target_exts=target_exts, excludes=excludes)

    @classmethod
    def task1(cls, src, dst, to_fmt):
        print("start task1: Monitoring dirs")
        cls._monitor = Monitor()
        cls._monitor.set_monitor(
            src_dir=src
            , dst_dir=dst
            , to_fmt=to_fmt
        )
        print("スタンバイ monitoring")
        cls._monitor.start_monitors()
        print("End task1")

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
    def task2(cls, smpl: Path, src: Path, target_ext: List[str], excludes: List[str]):
        """Copy sample dir's file to src dir"""
        msg = "Copy Task"
        print("Start " + msg)
        # 　monitorに投げるファイルPATHの抽出
        if len(target_ext) > 0:
            pattern = cls.pattener(target_ext)
            print("pattern: " + pattern)
            print("files_tmp", list(smpl.glob('*')))
            files = [p for p in smpl.glob('*') if re.search('.' + pattern, str(p))]
        else:
            files = smpl.glob('**/*')
        print("files:", list(files))
        for fn in files:
            if fn.suffix not in excludes:
                print("copy %s to %s" % (fn, src.as_posix()))
                shutil.copy(fn, src.as_posix())
        cls._complete_copy = True
        print("End " + msg)

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
        print("start " + msg)
        # src,dst dir内のfiles削除

        for a_path in (src, dst):
            print(f"Init: {a_path}")
            p_tmp = Path(a_path)
            files = p_tmp.glob('**/*')
            for a_file in files:
                a_file.unlink(missing_ok=False)
            # if os.path.exists(a_path):
            #     shutil.rmtree(a_path)
            # os.mkdir(a_path)
        print("cp1 task2")

    @classmethod
    def main(cls, sample: Path, src: Path, dst: Path, to_fmt: str, target_exts: List[str] = [], excludes: List[str] = []):
        print("main start")
        cls.init_dirs(src, dst)
        # files = sample.glob("*")
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="thread") as executor:
            e_task1 = executor.submit(cls.task1, src, dst, to_fmt)

            # for a_file in files:
            #     e_copy = executor.submit(cls.copy, a_file, src, excludes)
            #     while True:
            #         if e_copy.done():
            #             break
            e_task2 = executor.submit(cls.task2, sample, src, target_exts, excludes)
            states = [False] * 5
            while True:
                if len(states) > 5 and all(states) and cls._complete_copy:
                    break
                elif cls._monitor.state == StateMonitor.wait:
                    states.pop()
                    states.append(True)
                    time.sleep(2)
            print("main end")


if __name__ == "__main__":
    # AutoTester.start(target_exts=[".png"])
    AutoTester.start(to_fmt=".eps")
