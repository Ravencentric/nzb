from __future__ import annotations

import shutil
from pathlib import Path

from nzb import NZBMetaEditor, NZBParser

nzbs = Path("tests/__nzbs__").resolve()
encoding = "utf-8"


def test_meta_clear(tmp_path: Path) -> None:
    edited = nzbs / "spec_example_meta_clear.nzb"
    out = NZBMetaEditor.from_file(nzbs / "spec_example.nzb").clear().save(tmp_path / "spec_example_meta_clear.nzb")
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_nzb_with_no_head_clear(tmp_path: Path) -> None:
    nzb = nzbs / "nzb_with_no_head.nzb"
    out = NZBMetaEditor.from_file(nzb).clear().save(tmp_path / "nzb_with_no_head.nzb")
    assert out.is_file()


def test_meta_remove_append(tmp_path: Path) -> None:
    edited = nzbs / "spec_example_meta_append.nzb"
    out = (
        NZBMetaEditor.from_file(nzbs / "spec_example.nzb")
        .remove("password")
        .append(passwords="new secret!")
        .save(tmp_path / "spec_example.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_append_when_file_has_no_meta(tmp_path: Path) -> None:
    append = NZBMetaEditor.from_file(nzbs / "no_meta.nzb").append(title="appending").save(tmp_path / "no_meta.nzb")
    set = NZBMetaEditor.from_file(nzbs / "no_meta.nzb").set(title="appending").save(tmp_path / "no_meta.nzb")
    assert append.read_text(encoding).strip() == set.read_text(encoding).strip()


def test_meta_append_when_file_has_single_meta(tmp_path: Path) -> None:
    append = (
        NZBMetaEditor.from_file(nzbs / "single_meta.nzb").append(title="appending").save(tmp_path / "single_meta.nzb")
    )
    parsed = NZBParser.from_file(append).parse()
    assert parsed.meta.title == "appending"


def test_meta_remove_empty(tmp_path: Path) -> None:
    rm = (
        NZBMetaEditor.from_file(nzbs / "spec_example_meta_clear.nzb")
        .remove("category")
        .save(tmp_path / "spec_example_meta_clear.nzb")
    )
    parsed = NZBParser.from_file(rm).parse()
    assert parsed.meta.title is None
    assert parsed.meta.passwords is None
    assert parsed.meta.tags is None
    assert parsed.meta.category is None


def test_meta_remove_one(tmp_path: Path) -> None:
    rm = NZBMetaEditor.from_file(nzbs / "single_meta.nzb").remove("title").save(tmp_path / "single_meta.nzb")
    parsed = NZBParser.from_file(rm).parse()
    assert parsed.meta.title is None
    assert parsed.meta.passwords is None
    assert parsed.meta.tags is None
    assert parsed.meta.category is None


def test_meta_remove_missing_key(tmp_path: Path) -> None:
    rm = NZBMetaEditor.from_file(nzbs / "single_meta.nzb").remove("akldakldjakldjs").save(tmp_path / "single_meta.nzb")
    parsed = NZBParser.from_file(rm).parse()
    assert parsed.meta.title is not None
    assert parsed.meta.passwords is None
    assert parsed.meta.tags is None
    assert parsed.meta.category is None


def test_meta_set(tmp_path: Path) -> None:
    edited = nzbs / "spec_example_meta_set.nzb"
    out = (
        NZBMetaEditor.from_file(nzbs / "spec_example.nzb")
        .set(title="New title", tags=["test", "test2"])
        .save(tmp_path / "spec_example.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_set_empty(tmp_path: Path) -> None:
    edited = nzbs / "spec_example_meta_set.nzb"
    out = NZBMetaEditor.from_file(nzbs / "spec_example_meta_set.nzb").set().save(tmp_path / "spec_example_meta_set.nzb")
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_save_overwrite(tmp_path: Path) -> None:
    original = nzbs / "no_meta.nzb"
    tmp_nzb: Path = shutil.copy(original, tmp_path / "no_meta.nzb")
    NZBMetaEditor.from_file(tmp_nzb).save(overwrite=True)
    assert original.read_text(encoding).strip() == tmp_nzb.read_text(encoding).strip()


def test_no_doctype(tmp_path: Path) -> None:
    original = nzbs / "no_doctype.nzb"
    tmp_nzb: Path = shutil.copy(original, tmp_path / "no_doctype.nzb")
    NZBMetaEditor.from_file(tmp_nzb).save(overwrite=True)
    assert original.read_text(encoding).strip() == tmp_nzb.read_text(encoding).strip()
