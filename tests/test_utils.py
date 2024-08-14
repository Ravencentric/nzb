from __future__ import annotations

from nzb._utils import construct_meta_fields


def test_construct_meta_fields() -> None:
    assert construct_meta_fields(title="hello") == [{"@type": "title", "#text": "hello"}]
    assert construct_meta_fields(passwords="secret") == [{"@type": "password", "#text": "secret"}]
    assert construct_meta_fields(passwords=("secret", "secret2")) == [
        {"@type": "password", "#text": "secret"},
        {"@type": "password", "#text": "secret2"},
    ]
    assert construct_meta_fields(tags="hd") == [{"@type": "tag", "#text": "hd"}]
    assert construct_meta_fields(tags=("hd", "tv")) == [
        {"@type": "tag", "#text": "hd"},
        {"@type": "tag", "#text": "tv"},
    ]
    assert construct_meta_fields(category="cat") == [{"@type": "category", "#text": "cat"}]
