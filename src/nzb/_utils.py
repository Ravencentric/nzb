from __future__ import annotations

from functools import lru_cache
from typing import Callable, cast

from typing_extensions import ParamSpec, TypeVar

from nzb._types import CollectionOf

T = TypeVar("T")
P = ParamSpec("P")


def cache(func: Callable[P, T], /) -> Callable[P, T]:
    """Identical to functools.cache but with typing"""
    return cast(Callable[P, T], lru_cache(maxsize=None)(func))


def construct_meta_fields(
    title: str | None = None,
    passwords: CollectionOf[str] | str | None = None,
    tags: CollectionOf[str] | str | None = None,
    category: str | None = None,
) -> list[dict[str, str]]:
    """
    Constructor that constructs valid `<meta> .. </meta>` fields
    """

    meta = []

    if title:
        meta.append({"@type": "title", "#text": title})

    if passwords:
        if isinstance(passwords, str):
            meta.append({"@type": "password", "#text": passwords})
        else:
            for password in passwords:
                meta.append({"@type": "password", "#text": password})

    if tags:
        if isinstance(tags, str):
            meta.append({"@type": "tag", "#text": tags})
        else:
            for tag in tags:
                meta.append({"@type": "tag", "#text": tag})

    if category:
        meta.append({"@type": "category", "#text": category})

    return meta
