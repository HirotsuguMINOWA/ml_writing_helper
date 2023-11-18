from pathlib import Path
from ml_writing_helper import Monitor  # MLWritingHelperでもml_writing_helperでよい？

o = Monitor()

# defines manuscript root path
manuscript_root = Path(__file__).resolve().parent

# monitoring fig_src folder and it converts their files into fid_gen.
o.set_monitor(
    src_dir=manuscript_root.joinpath("fig_src"),
    dst_dir=manuscript_root.joinpath("fig_gen"),
    to_fmt=".eps",
)

# o.set_monitor(
#     src_dir="/Users/my_user/Documents/BibTexExported",
#     dst_dir=manuscript_root.joinpath("bib"),
#     to_fmt=".bib",
# )

# Start monitoring target folders
o.start_monitors()
