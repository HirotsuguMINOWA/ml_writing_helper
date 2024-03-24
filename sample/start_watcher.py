from pathlib import Path

import click
from loguru import logger
from ml_writing_helper import Monitor
from ml_writing_helper.output_ext import OutputExtTuple

o = Monitor()


@click.command()
@click.option('--ext', type=click.Choice(OutputExtTuple))  # , default='pdf')
def run(ext: str = "pdf"):
    """defines manuscript root path"""
    manuscript_root = Path(__file__).resolve().parent
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
    # o.set_monitor(
    #     src_dir="/Users/my_user/Documents/BibTexExported",
    #     dst_dir=manuscript_root.joinpath("bib"),
    #     to_fmt=".bib",
    # )

    """Start monitoring target folders"""
    o.start_monitors()


if __name__ == "__main__":
    run()
