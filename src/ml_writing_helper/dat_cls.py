from dataclasses import dataclass
from pathlib import Path
from loguru import logger
from src.ml_writing_helper.extension import TaskType


@dataclass
class ObserverInstance:
    task_type: TaskType


@dataclass
class CopyTaskPrimitive:
    src_path: str | Path
    dest_path: str | Path


@dataclass
class ImgConvTaskStruct(ObserverInstance, CopyTaskPrimitive):
    gray: bool = False
    is_crop: bool = True
    mk_dst_dir: bool = True


@dataclass
class CopyTask(ObserverInstance, CopyTaskPrimitive):
    pass


def test_1() -> None:
    ins = ImgConvTaskStruct(task_type=TaskType.copy, dest_path="./tmp_dest", src_path="./tmp_src")
    logger.success(ins)


if __name__ == "__main__":
    test_1()
