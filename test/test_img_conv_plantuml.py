"""--mode img_conv で PlantUML(.pu/.puml) を画像へ変換するテスト (plantuml コマンドが必要)"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image

from ml_writing_helper.converter.slide_img_converter import ImgConvInputType
from ml_writing_helper.task_runner.img_conv_runner import ImgConvTaskStruct

FIG_SAMPLE = Path(__file__).resolve().parent / "fig_sample"

needs_plantuml = pytest.mark.skipif(shutil.which("plantuml") is None, reason="plantuml command not found")


def test_plantuml_suffixes_are_img_conv_sources() -> None:
    assert "pu" in tuple(ImgConvInputType)
    assert "puml" in tuple(ImgConvInputType)


@needs_plantuml
@pytest.mark.parametrize("ext", ["png", "pdf", "eps", "jpg", "gif", "bmp", "tiff"])
def test_plantuml_to_each_format(tmp_path: Path, ext: str) -> None:
    src = tmp_path / "fig src"  # 空白を含むPATHでも変換できること
    (src / "sub").mkdir(parents=True)
    _ = shutil.copy(FIG_SAMPLE / "test_puml.puml", src)
    _ = shutil.copy(FIG_SAMPLE / "test_pu.pu", src / "sub")
    dst = tmp_path / "fig gen"
    dst.mkdir()

    ImgConvTaskStruct(src_dir_path=src, dst_dir_path=dst, dst_suffix=ext).run_all_target_files_in_target_dir()

    for out in (dst / f"test_puml.{ext}", dst / "sub" / f"test_pu.{ext}"):
        assert out.is_file() and out.stat().st_size > 0, out


@needs_plantuml
def test_plantuml_gray(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    _ = shutil.copy(FIG_SAMPLE / "test_puml.puml", src)
    dst = tmp_path / "dst"
    dst.mkdir()

    ImgConvTaskStruct(src_dir_path=src, dst_dir_path=dst, dst_suffix="png", gray=True).run_all_target_files_in_target_dir()

    with Image.open(dst / "test_puml.png") as im:
        assert im.mode == "L"
