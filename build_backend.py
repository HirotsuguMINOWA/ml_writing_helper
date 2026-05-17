"""PEP 517 backend wrapper for building Nuitka wheels in non-ASCII paths."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


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

if not LEGACY_EDITABLE:
    from nuitka.distutils.Build import (  # noqa: E402
        build_editable,
        get_requires_for_build_editable,
        prepare_metadata_for_build_editable,
    )
