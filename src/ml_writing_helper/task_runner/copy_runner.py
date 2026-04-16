# @dataclass
from collections.abc import Sequence
from pathlib import Path
from typing import override

from typed_classproperties import cached_classproperty

from ml_writing_helper.enum_cls import TaskType
from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner


class CopyTask(ABCTaskRunner):
    @cached_classproperty
    def target_src_exts(cls) ->  Sequence[str]:
        return None

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.copy

    """監視下で.bibの様に変更があればcopyする処理をするクラス"""

    @override
    def dest_file_path(self, update_file_path: Path) -> Path:
        if self._dest_dir_path.suffix:
            return self._dest_dir_path
        return self._dest_dir_path / update_file_path.name

    @override
    def run(self, update_file_path: Path) -> None:
        if not self._match(update_file_path=update_file_path):
            return
        self.copy_in_timestamp_ins(update_file_path=update_file_path)
