test_img = "test.jpg"

from pathlib import Path
from src.watcher_pptx2pdf import ChangeHandler
from subprocess import check_output, STDOUT
import shlex


def run_cmd(cmd: str, is_print=True):
    """
    コマンド(CLI)の実行
    :param cmd:
    :param is_print:
    :return:
    """
    if is_print:
        print("cmd:%s" % cmd)
    tokens = shlex.split(cmd)
    # subprocess.run(tokens)
    output = check_output(tokens, stderr=STDOUT).decode("utf8")
    if is_print:
        print("Output: %s" % output)
    return output


p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dst = Path(__file__).resolve().parent.joinpath("fig_tmp")

p_target = p_src.joinpath(test_img)
if p_target.exists():
    run_cmd("rm %s" % p_target)

tmp = p_dst.joinpath(test_img)
if tmp.exists():
    run_cmd("rm %s" % tmp)

print("テスト用画像(%s)ファイルを手動で%sへコピーしろ" % (test_img, p_dst.name))

ChangeHandler(
    monitoring_dir=p_src.as_posix(), output_dir=p_dst.as_posix()
    , dst_ext_no_period="eps"
).start()

# FIXME: 上記で制御が戻ってこないので、下記実行されず
run_cmd("cp %s %s" % (p_target, p_src.joinpath(test_img)))
