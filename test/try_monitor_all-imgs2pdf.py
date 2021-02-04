# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
# and need set working dir at prj root(ml_writing_helper)
import os
import shutil
import sys
from pathlib import Path

# sys.path.append("/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/src")
from typing import List

sys.path.append("../src")
from core import ChangeHandler
import concurrent.futures
import time
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import glob


# from logging import StreamHandler, Formatter, INFO, getLogger


class AutoTester:

    @classmethod
    def start(cls, sample="fig_sample", src="fig_src", dst="fig_gen", to_fmt=".eps", exe_ext=[]):
        cls.to_fmt = to_fmt
        cls.src = src
        cls.sample = sample
        cls.dst = dst

        cls.exc_ext = exe_ext

        cls.e_task1 = None
        cls.main(sample=Path(sample), src=Path(src), dst=Path(dst), to_fmt=to_fmt, excludes=exe_ext)

    @staticmethod
    def task1(src, dst, to_fmt):
        print("start task1: Monitoring dirs")
        p = ChangeHandler()
        p.set_monitor(
            src_dir=src
            , dst_dir=dst
            , to_fmt=to_fmt
        )
        print("スタンバイ monitoring")
        p.start_monitors()
        print("End task1")

    @classmethod
    def task2(cls):
        """Copy sample dir's file to src dir"""
        msg = "Task2: Copy files to src dir"
        print("start " + msg)
        # src,dst dir内のfiles削除

        for a_path in (cls.src, cls.dst):
            print(f"Init: {a_path}")
            p_tmp = Path(a_path)
            files = p_tmp.glob('**/*')
            for a_file in files:
                a_file.unlink(missing_ok=False)
            # if os.path.exists(a_path):
            #     shutil.rmtree(a_path)
            # os.mkdir(a_path)
        print("cp1 task2")
        smpl = Path(cls.sample)
        print("samples:%s" % smpl)
        for fn in smpl.glob("*"):
            if fn.suffix not in cls.exc_ext:
                print("copy %s to %s" % (fn, cls.src))
                shutil.copy(fn, cls.src)
        print("End " + msg)
        # e_task1.cancel()  # FIXME: 効いていない

    @staticmethod
    def copy(a_file: Path, src: Path, excludes):
        if a_file.suffix not in excludes:
            print(f"copy {a_file} to {src}")
            shutil.copy(a_file, src)

    @staticmethod
    def init_dirs(src, dst):
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
    def main(cls, sample: Path, src: Path, dst: Path, to_fmt: str, excludes: List[str]):
        print("main start")
        cls.init_dirs(src, dst)
        files = sample.glob("*")
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="thread") as executor:
            e_task1 = executor.submit(cls.task1, src, dst, to_fmt)
            # time.sleep(0.5)
            # print(f"Result task1: {e_task1.result()}")
            # e_task2 = executor.submit(cls.task2)
            # print(f"Result task2: {e_task2.result()}")
            for a_file in files:
                e_copy = executor.submit(cls.copy, a_file, src, excludes)
                while True:
                    if e_copy.done():
                        break

            while True:
                if e_copy.done():
                    break
                time.sleep(1000)
            # # getLogger().info("submit end")
            # #
            # #
            # print("End of submit threads")
            # # for f in futures.as_completed(wait_for):
            # #     print('main: result: {}'.format(f.result()))
            # print("start loop in converting")
            # while True:
            #     # TODO:  task2が終わったらプログラム終わりにしたい˝
            #     time.sleep(10)
            #     if e_task2.done():
            #         e_task1.cancel()
            print("main end")


if __name__ == "__main__":
    AutoTester.start()
