from pathlib import Path

import click
from loguru import logger
from src.ml_writing_helper.enum_cls import OutputExtTuple
from src.ml_writing_helper import Monitor

o = Monitor()

manuscript_root = Path(__file__).resolve().parent
src_p:Path=manuscript_root.joinpath("src")
dst_p:Path=manuscript_root.joinpath("dst")

@click.command()
@click.option('--ext', type=click.Choice(OutputExtTuple))  # , default='pdf')
def start_watching(ext: str = "pdf"):
    """defines manuscript root path"""

    logger.debug(f"manuscript_root: {manuscript_root}")

    """monitoring fig_src folder and it converts their files into fid_gen."""
    o.set_monitor(
        src_dir=manuscript_root.joinpath("fig_src"),
        dst_dir=manuscript_root.joinpath("fig_gen"),
        to_fmt=f".{ext}",
        is_crop=True,
        mk_dst_dir=True,
        gray=True,
    )

    """out of project bib file monitoring. If changed, it copies to the bib folder."""
    o.set_copy_task(
        src_dir="/Users/my_user/Documents/BibTexExported",
        dst_dir=manuscript_root.joinpath("bib"),
        src_suffixes=["bib"],
    )

    """Start monitoring target folders"""
    o.start_monitors()


if __name__ == "__main__":
    run()
