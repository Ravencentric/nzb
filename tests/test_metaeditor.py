from __future__ import annotations

import shutil
from pathlib import Path

from nzb import Nzb, NzbMetaEditor

NZB_DIR = Path(__file__).parent.resolve() / "__nzbs__"
encoding = "utf-8"


def test_meta_clear(tmp_path: Path) -> None:
    edited = NZB_DIR / "spec_example_meta_clear.nzb"
    out = (
        NzbMetaEditor.from_file(NZB_DIR / "spec_example.nzb").clear().to_file(tmp_path / "spec_example_meta_clear.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_nzb_with_no_head_clear(tmp_path: Path) -> None:
    nzb = NZB_DIR / "nzb_with_no_head.nzb"
    out = NzbMetaEditor.from_file(nzb).clear().to_file(tmp_path / "nzb_with_no_head.nzb")
    assert out.is_file()


def test_meta_remove_append(tmp_path: Path) -> None:
    edited = NZB_DIR / "spec_example_meta_append.nzb"
    out = (
        NzbMetaEditor.from_file(NZB_DIR / "spec_example.nzb")
        .remove("password")
        .append(passwords="new secret!")
        .to_file(tmp_path / "spec_example.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_append_when_file_has_no_meta(tmp_path: Path) -> None:
    append = (
        NzbMetaEditor.from_file(NZB_DIR / "no_meta.nzb")
        .append(title="appending")
        .to_file(tmp_path / "no_meta_append.nzb")
    )
    set = NzbMetaEditor.from_file(NZB_DIR / "no_meta.nzb").set(title="appending").to_file(tmp_path / "no_meta_set.nzb")
    assert append.read_text(encoding).strip() == set.read_text(encoding).strip()


def test_meta_append_when_file_has_single_meta(tmp_path: Path) -> None:
    append = (
        NzbMetaEditor.from_file(NZB_DIR / "single_meta.nzb")
        .append(title="appending")
        .to_file(tmp_path / "single_meta.nzb")
    )
    parsed = Nzb.from_file(append)
    assert parsed.meta.title == "appending"


def test_meta_remove_empty(tmp_path: Path) -> None:
    rm = (
        NzbMetaEditor.from_file(NZB_DIR / "spec_example_meta_clear.nzb")
        .remove("category")
        .to_file(tmp_path / "spec_example_meta_clear.nzb")
    )
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_remove_one(tmp_path: Path) -> None:
    rm = NzbMetaEditor.from_file(NZB_DIR / "single_meta.nzb").remove("title").to_file(tmp_path / "single_meta.nzb")
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_remove_missing_key(tmp_path: Path) -> None:
    rm = (
        NzbMetaEditor.from_file(NZB_DIR / "single_meta.nzb")
        .remove("akldakldjakldjs")
        .to_file(tmp_path / "single_meta.nzb")
    )
    parsed = Nzb.from_file(rm)
    assert parsed.meta.title is not None
    assert parsed.meta.passwords == ()
    assert parsed.meta.tags == ()
    assert parsed.meta.category is None


def test_meta_set(tmp_path: Path) -> None:
    edited = NZB_DIR / "spec_example_meta_set.nzb"
    out = (
        NzbMetaEditor.from_file(NZB_DIR / "spec_example.nzb")
        .set(title="New title", tags=["test", "test2"])
        .to_file(tmp_path / "spec_example.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_set_empty(tmp_path: Path) -> None:
    edited = NZB_DIR / "spec_example_meta_set.nzb"
    out = (
        NzbMetaEditor.from_file(NZB_DIR / "spec_example_meta_set.nzb")
        .set()
        .to_file(tmp_path / "spec_example_meta_set.nzb")
    )
    assert out.read_text(encoding).strip() == edited.read_text(encoding).strip()


def test_meta_save_overwrite(tmp_path: Path) -> None:
    original = NZB_DIR / "no_meta.nzb"
    tmp_nzb: Path = shutil.copy(original, tmp_path / "no_meta.nzb")
    NzbMetaEditor.from_file(tmp_nzb).to_file(tmp_nzb, overwrite=True)
    assert original.read_text(encoding).strip() == tmp_nzb.read_text(encoding).strip()


def test_no_doctype(tmp_path: Path) -> None:
    original = NZB_DIR / "no_doctype.nzb"
    tmp_nzb: Path = shutil.copy(original, tmp_path / "no_doctype.nzb")
    NzbMetaEditor.from_file(tmp_nzb).to_file(tmp_nzb, overwrite=True)
    assert original.read_text(encoding).strip() == tmp_nzb.read_text(encoding).strip()
