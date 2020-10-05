"""
.pumlの変換のtrialコード
"""
import logging
from pathlib import Path

from logger_getter import get_logger
from src.core import ChangeHandler, logger

logger = get_logger(level_console=logging.DEBUG, name=__file__)
ChangeHandler(logger_=logger).conv_plantuml(Path("sample/fig_src/test_puml.puml"), Path("sample/fig_src/gen_pu2png.png"))
