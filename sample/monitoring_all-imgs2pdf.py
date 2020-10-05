# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
import os
import shutil
import sys
from pathlib import Path
from core import ChangeHandler
import concurrent.futures
import time
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor

# from logging import StreamHandler, Formatter, INFO, getLogger

to_fmt = ".pdf"
src = "fig_src"
sample = "fig_sample"
dst = "fig_gen"
# exc_ext = [".odp"]
exc_ext = []

e_task1 = None


def task1():
    print("start task1")
    p = ChangeHandler()
    p.set_monitor(
        src_dir=src
        , dst_dir=dst
        , to_fmt=to_fmt
    )
    print("before monitoring")
    p.start_monitors()
    print("end task1")


def task2():
    print("start task2")
    for name in (src, dst):
        if os.path.exists(name):
            shutil.rmtree(name)
        os.mkdir(name)
    print("cp1 task2")
    smpl = Path(sample)
    print("samples:%s" % smpl)
    for fn in smpl.glob("*"):
        if fn.suffix not in exc_ext:
            print("copy %s to %s" % (fn, src))
            shutil.copy(fn, src)
    print("end task2")
    e_task1.cancel()  # FIXME: 効いていない


print("main start")
with ThreadPoolExecutor(max_workers=2, thread_name_prefix="thread") as executor:
    e_task1 = executor.submit(task1)
    # time.sleep(0.5)
    executor.submit(task2)
    # getLogger().info("submit end")
    print("submit end")
# for f in futures.as_completed(wait_for):
#     print('main: result: {}'.format(f.result()))
while True:
    # task2が終わったらプログラム終わりにしたい˝
    time.sleep(1)
print("main end")
