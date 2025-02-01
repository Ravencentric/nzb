from __future__ import annotations

from nzb._utils import construct_meta, remove_meta_fields, sort_meta


def test_construct_meta() -> None:
    assert construct_meta(title="hello") == [{"@type": "title", "#text": "hello"}]
    assert construct_meta(passwords="secret") == [{"@type": "password", "#text": "secret"}]
    assert construct_meta(passwords=("secret", "secret2")) == [
        {"@type": "password", "#text": "secret"},
        {"@type": "password", "#text": "secret2"},
    ]
    assert construct_meta(tags="hd") == [{"@type": "tag", "#text": "hd"}]
    assert construct_meta(tags=("hd", "tv")) == [
        {"@type": "tag", "#text": "hd"},
        {"@type": "tag", "#text": "tv"},
    ]
    assert construct_meta(category="cat") == [{"@type": "category", "#text": "cat"}]


def test_sort_meta_list() -> None:
    meta = [
        {"@type": "category", "#text": "test"},
        {"@type": "title", "#text": "test"},
        {"@type": "unknown", "#text": "test"},
    ]
    assert sort_meta(meta) == [
        {"@type": "unknown", "#text": "test"},
        {"@type": "title", "#text": "test"},
        {"@type": "category", "#text": "test"},
    ]


def test_sort_meta_mixed_case_list() -> None:
    meta = [
        {"@type": "TAG", "#text": "test"},
        {"@type": "Password", "#text": "test"},
        {"@type": "title", "#text": "test"},
    ]
    assert sort_meta(meta) == [
        {"@type": "title", "#text": "test"},
        {"@type": "Password", "#text": "test"},
        {"@type": "TAG", "#text": "test"},
    ]


def test_remove_meta_fields_duplicates() -> None:
    meta = [
        {"@type": "title", "#text": "test"},
        {"@type": "title", "#text": "test2"},
        {"@type": "category", "#text": "test"},
    ]
    assert remove_meta_fields(meta, ["title"]) == [{"@type": "category", "#text": "test"}]


def test_remove_meta_fields_none() -> None:
    meta = [
        {"@type": "title", "#text": "test"},
        {"@type": "title", "#text": "test2"},
        {"@type": "category", "#text": "test"},
    ]
    assert remove_meta_fields(meta) == meta


def test_remove_meta_fields_empty_type() -> None:
    meta = [{"@type": "", "#text": "test"}, {"@type": "category", "#text": "test"}]
    assert remove_meta_fields(meta, ["title"]) == meta
