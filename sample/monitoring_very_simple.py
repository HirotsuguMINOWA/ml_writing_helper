from src.watcher_pptx2pdf import ChangeHandler
from pathlib import Path

ChangeHandler(
    monitoring_dir="fig_src", output_dir="fig_gen"
    , dest_ext_no_period="eps"
).start()
