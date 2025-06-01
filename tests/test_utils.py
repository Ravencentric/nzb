from __future__ import annotations

import pytest

from nzb._utils import to_iterable


def test_to_iterable() -> None:
    assert to_iterable("hello") == ("hello",)
    assert to_iterable(None) == ()
    assert to_iterable(["a", "b", "c"]) == ["a", "b", "c"]

    with pytest.raises(TypeError):
        to_iterable(object())  # type: ignore[arg-type]
