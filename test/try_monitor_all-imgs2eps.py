# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
# and need set working dir at prj root(ml_writing_helper)
import os
import shutil
import sys
from pathlib import Path
from core import ChangeHandler
import concurrent.futures
import time
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import glob



# from logging import StreamHandler, Formatter, INFO, getLogger

to_fmt = ".eps"
src = "fig_src"
sample = "fig_sample"
dst = "fig_gen"
exc_ext = []

e_task1 = None


def task1():
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


def task2():
    """Copy sample dir's file to src dir"""
    msg = "Task2: Copy files to src dir"
    print("start " + msg)
    # src,dst dir内のfiles削除


    for a_path in (src, dst):
        print(f"Init: {a_path}")
        p_tmp = Path(a_path)
        files=p_tmp.glob('**/*')
        for a_file in files:
            a_file.unlink(missing_ok=False)
        # if os.path.exists(a_path):
        #     shutil.rmtree(a_path)
        # os.mkdir(a_path)
    print("cp1 task2")
    smpl = Path(sample)
    print("samples:%s" % smpl)
    for fn in smpl.glob("*"):
        if fn.suffix not in exc_ext:
            print("copy %s to %s" % (fn, src))
            shutil.copy(fn, src)
    print("End " + msg)
    #e_task1.cancel()  # FIXME: 効いていない


print("main start")
with ThreadPoolExecutor(max_workers=2, thread_name_prefix="thread") as executor:
    e_task1 = executor.submit(task1)
    # time.sleep(0.5)
    e_task2 = executor.submit(task2)
    print(f"Result task1: {e_task1.result()}")
    print(f"Result task2: {e_task2.result()}")

    # getLogger().info("submit end")
    #
    #
    print("End of submit threads")
    # for f in futures.as_completed(wait_for):
    #     print('main: result: {}'.format(f.result()))
    print("start loop in converting")
    while True:
        # TODO:  task2が終わったらプログラム終わりにしたい˝
        time.sleep(10)
        if e_task2.done():
            e_task1.cancel()
    print("main end")
