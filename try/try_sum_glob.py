"""
.globメソッドを使って、複数の拡張子指定したファイルの抽出の試み
"""
import re
from pathlib import Path
from typing import List


def pattener(target_ext: List[str]) -> str:
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


def main(smpl: Path, target_ext: List[str]):
    pattern = pattener(target_ext)
    print(f"pattern:{pattern}")
    files = [p for p in smpl.glob('**/*') if re.search('.' + pattern, str(p))]
    return files


if __name__ == "__main__":
    # target_ext = [".png", ".eps"]
    target_ext = [".png"]
    smpl = Path("fig_sample")
    files = main(smpl, target_ext)
    print(files)
