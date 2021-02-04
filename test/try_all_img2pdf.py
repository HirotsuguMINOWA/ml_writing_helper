"""
Test to convert all images in fig_src into .pdf files.
"""
from try_all_img2eps import AutoTester

a = AutoTester()
# a.start(to_fmt=".eps", target_exts=[".png"])
a.start(to_fmt=".pdf")
