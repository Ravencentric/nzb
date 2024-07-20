from pathlib import Path

import pytest
from nzb import InvalidNZBError, NZBMetaEditor, NZBParser

nzbs = Path("tests/__nzbs__/")


def test_saving_without_filename() -> None:
    with pytest.raises(FileNotFoundError):
        NZBMetaEditor((nzbs / "spec_example.nzb").read_text()).save()


def test_saving_overwrite() -> None:
    with pytest.raises(FileExistsError):
        NZBMetaEditor.from_file(nzbs / "spec_example.nzb").save()


def test_parser_exceptions() -> None:
    with pytest.raises(InvalidNZBError):
        NZBParser.from_file(nzbs / "malformed_files.nzb").parse()

    with pytest.raises(InvalidNZBError):
        NZBParser.from_file(nzbs / "malformed_files2.nzb").parse()

    with pytest.raises(InvalidNZBError):
        NZBParser.from_file(nzbs / "malformed_groups.nzb").parse()

    with pytest.raises(InvalidNZBError):
        NZBParser.from_file(nzbs / "malformed_segments.nzb").parse()
