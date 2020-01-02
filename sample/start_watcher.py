from src.watcher_pptx2pdf import ChangeHandler
from pathlib import Path

cwd = Path("Manuscript")
# p_src=cwd/"fig_src"
# p_dest=cwd/"fig_tmp"
# p_src=Path(".").joinpath("fig_src")
# p_dest=Path(".").joinpath("fig_tmp")
# p_src=Path(__file__).resolve().parent.joinpath("fig_src")
# p_dest=Path(__file__).resolve().parent.joinpath("fig_tmp")
p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dest = Path(__file__).resolve().parent.joinpath("fig_tmp")
ChangeHandler(
    monitoring_dir=p_src.as_posix(), output_dir=p_dest.as_posix()
    , dest_ext_no_period="png"
).start()
