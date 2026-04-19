#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nuitkaを使って ml_writing_helper を単一実行ファイルにビルドするスクリプト。

Usage:
    python build_nuitka.py
    python build_nuitka.py --onefile
    python build_nuitka.py --debug
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_ROOT / "src" / "ml_writing_helper" / "main.py"
OUTPUT_DIR = PROJECT_ROOT / "build_nuitka_output"
OUTPUT_NAME = "ml_writing_helper"

# --- Options ---
onefile = "--onefile" in sys.argv
debug = "--debug" in sys.argv


def check_nuitka():
    """Nuitkaがインストールされているか確認"""
    try:
        import nuitka
        # print(f"Nuitka version: {nuitka.__version__}")
    except ImportError:
        print("Error: Nuitkaがインストールされていません。")
        print("インストールするには: pip install nuitka")
        sys.exit(1)


def build():
    """Nuitkaでビルドを実行"""
    check_nuitka()

    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ビルドコマンドの組み立て
    cmd = [
        sys.executable, "-m", "nuitka",
        # "--standalone",
        "--output-dir=" + str(OUTPUT_DIR),
        "--output-filename=" + OUTPUT_NAME,
        # "--mode=onefile",
        # "--enable-plugin=numpy",
        "--include-data-dir=src=src",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=Tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=pandas",
        "--nofollow-import-to=kiwisolver",
        "--nofollow-import-to=sqlite",
        # pdfCropMarginsの一部削って軽くする手筈、エラー生じたら、コメントアウトせよ
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=PySimpleGUI",
        "--nofollow-import-to=pdfCropMargins.gui",
        str(SOURCE_FILE),
    ]

    if onefile:  # ! "--onefileと印加せよ"
        # cmd.append("--onefile")
        cmd.append("--output-mode=single-file")
        print("Mode: --onefile (単一実行ファイル)")
    else:
        print("Mode: --onefile=disable (ディレクトリ出力)")

    if debug:
        cmd.append("--debug=full")
        print("Debug mode: enabled")

    # macOS-specific: macOS catalystを無効化
    if platform.system() == "Darwin":
        # cmd.append("--macos-app-name=ml_writing_helper")
        # cmd.append("--macos-app-mode=gui")
        pass
    # cmd.append('--mode=app')  # MacOSの時表示された。Winなどで必要化は不明
    print(f"\nBuilding...")
    print(f"Command: {' '.join(cmd)}\n")

    # ビルド実行
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("Build successful!")
        if onefile:
            dist_path = OUTPUT_DIR / f"{OUTPUT_NAME}.dist" / OUTPUT_NAME
        else:
            dist_path = OUTPUT_DIR / f"{OUTPUT_NAME}.dist"
        print(f"Output: {dist_path}")
        print("=" * 50)
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    build()
