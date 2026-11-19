"""PEP 517 backend wrapper for building Nuitka wheels in non-ASCII paths."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


_ROOT = Path(__file__).resolve().parent
_VERSION_FILE = _ROOT / "VERSION.txt"


def _write_version_file() -> None:
    """Write today's date (calver) to VERSION.txt so setuptools can read it.

    pipx (and pip) run the build in an isolated directory where VERSION.txt
    may not exist. Generating it here guarantees a non-``0.0.0`` version even
    when no pre-build hook has been executed.
    """
    _VERSION_FILE.write_text(datetime.now().strftime("%Y.%m.%d") + "\n", encoding="utf-8")


def _parse_compilation_report(filename):
    """Read Nuitka XML reports as UTF-8 even when the XML header says utf8."""
    report_file = Path(filename)
    if not report_file.is_file():
        return None

    text = report_file.read_text(encoding="utf-8")
    return ElementTree.fromstring(
        text.replace("encoding='utf8'", "encoding='UTF-8'", 1)
    )


def _patch_nuitka_report_reader():
    from nuitka.reports import CompilationReportReader

    CompilationReportReader.parseCompilationReport = _parse_compilation_report

    try:
        from nuitka.distutils import DistutilsCommands
    except ImportError:
        return

    DistutilsCommands.parseCompilationReport = _parse_compilation_report


_patch_nuitka_report_reader()

from nuitka.distutils.Build import (  # noqa: E402
    LEGACY_EDITABLE,
    build_sdist,
    build_wheel,
    get_requires_for_build_sdist,
    get_requires_for_build_wheel,
    prepare_metadata_for_build_wheel,
)

# ラップ: メタデータ準備/ホイールビルド前に VERSION.txt を必ず生成する
_orig_prepare_metadata_for_build_wheel = prepare_metadata_for_build_wheel
_orig_build_wheel = build_wheel


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    _write_version_file()
    return _orig_prepare_metadata_for_build_wheel(
        metadata_directory, config_settings
    )


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    _write_version_file()
    return _orig_build_wheel(wheel_directory, config_settings, metadata_directory)


if not LEGACY_EDITABLE:
    from nuitka.distutils.Build import (  # noqa: E402
        build_editable,
        get_requires_for_build_editable,
        prepare_metadata_for_build_editable,
    )

    _orig_prepare_metadata_for_build_editable = prepare_metadata_for_build_editable

    def prepare_metadata_for_build_editable(
        metadata_directory, config_settings=None
    ):
        _write_version_file()
        return _orig_prepare_metadata_for_build_editable(
            metadata_directory, config_settings
        )
