from typing import Literal

OutputExtTuple = tuple(['png', 'pdf', 'jpeg', 'jpg', 'bmp', 'gif', 'tiff', 'eps'])  # '.webp', '.svg',
OutputExtTypeLiteral = Literal[OutputExtTuple]
