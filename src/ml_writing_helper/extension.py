from strenum import StrEnum
from typing import Literal


class FormatInput(StrEnum):
    png = ".png"
    jpeg = ".jpeg"
    pdf = ".pdf"
    none = "none"


OutputExtTuple = tuple(['png', 'pdf', 'jpeg', 'jpg', 'bmp', 'gif', 'tiff', 'eps'])  # '.webp', '.svg',
OutputExtTypeLiteral = Literal[OutputExtTuple]
