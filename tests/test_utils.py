from __future__ import annotations

from nzb._utils import meta_constructor


def test_meta_constructor() -> None:
    assert meta_constructor(title="hello") == [{"@type": "title", "#text": "hello"}]
    assert meta_constructor(passwords="secret") == [{"@type": "password", "#text": "secret"}]
    assert meta_constructor(passwords=("secret", "secret2")) == [
        {"@type": "password", "#text": "secret"},
        {"@type": "password", "#text": "secret2"},
    ]
    assert meta_constructor(tags="hd") == [{"@type": "tag", "#text": "hd"}]
    assert meta_constructor(tags=("hd", "tv")) == [
        {"@type": "tag", "#text": "hd"},
        {"@type": "tag", "#text": "tv"},
    ]
    assert meta_constructor(category="cat") == [{"@type": "category", "#text": "cat"}]
