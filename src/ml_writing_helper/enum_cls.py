from enum import Enum, auto, StrEnum
from typing import Literal


class FormatInput(StrEnum):
    png = ".png"
    jpeg = ".jpeg"
    pdf = ".pdf"
    none = "none"


class TaskType(StrEnum):
    copy = auto()
    img_conv = auto()


class ImgConvType(StrEnum):
    jpg = auto()
    png = auto()
    eps = auto()


class MethodToFixEPS(StrEnum):
    gs = "gs"
    eps_pdf_converter = "eps2pdf&pdf2eps"


class StateMonitor(Enum):
    wait = auto()
    convert = auto()


OutputExtTuple = tuple(['png', 'pdf', 'jpeg', 'jpg', 'bmp', 'gif', 'tiff', 'eps'])  # '.webp', '.svg',
OutputExtTypeLiteral = Literal[OutputExtTuple]
