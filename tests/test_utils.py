from __future__ import annotations

import random

import pytest

from nzb._utils import sort_key_from_subject, to_iterable


def test_to_iterable() -> None:
    assert to_iterable("hello") == ("hello",)
    assert to_iterable(None) == ()
    assert to_iterable(["a", "b", "c"]) == ["a", "b", "c"]

    with pytest.raises(TypeError):
        to_iterable(object())  # type: ignore[arg-type]


def test_sort_key_from_subject() -> None:
    assert (
        sort_key_from_subject('[10/141] - "00010.clpi" yEnc (1/1) 1000') == '[010/141] - "00010.clpi" yEnc (1/1) 1000'
    )
    assert sort_key_from_subject('"00010.clpi" yEnc (1/1) 1000') == '"00010.clpi" yEnc (1/1) 1000'
    control = [
        '[1/141] - "00001.clpi" yEnc (1/1) 24248',
        '[2/141] - "00002.clpi" yEnc (1/1) 860',
        '[3/141] - "00003.clpi" yEnc (1/1) 480',
        '[4/141] - "00004.clpi" yEnc (1/1) 1136',
        '[5/141] - "00005.clpi" yEnc (1/1) 480',
        '[6/141] - "00006.clpi" yEnc (1/1) 480',
        '[7/141] - "00007.clpi" yEnc (1/1) 712',
        '[8/141] - "00008.clpi" yEnc (1/1) 392',
        '[9/141] - "00009.clpi" yEnc (1/1) 1016',
        '[10/141] - "00010.clpi" yEnc (1/1) 1000',
        '[11/141] - "00011.clpi" yEnc (1/1) 296',
        '[12/141] - "00012.clpi" yEnc (1/1) 296',
        '[13/141] - "00013.clpi" yEnc (1/1) 332',
        '[14/141] - "00014.clpi" yEnc (1/1) 332',
        '[15/141] - "MovieObject.bdmv" yEnc (1/1) 39430',
        '[16/141] - "00001.mpls" yEnc (1/1) 708',
        '[17/141] - "00002.mpls" yEnc (1/1) 188',
        '[18/141] - "00003.mpls" yEnc (1/1) 188',
        '[19/141] - "00004.mpls" yEnc (1/1) 188',
        '[20/141] - "00005.mpls" yEnc (1/1) 188',
        '[21/141] - "00006.mpls" yEnc (1/1) 188',
        '[22/141] - "00007.mpls" yEnc (1/1) 188',
        '[23/141] - "00008.mpls" yEnc (1/1) 174',
        '[24/141] - "00009.mpls" yEnc (1/1) 13046',
        '[25/141] - "00010.mpls" yEnc (1/1) 158',
        '[26/141] - "00011.mpls" yEnc (1/1) 158',
        '[27/141] - "index.bdmv" yEnc (1/1) 280',
        '[28/141] - "00001.clpi" yEnc (1/1) 24248',
        '[29/141] - "00002.clpi" yEnc (1/1) 860',
        '[30/141] - "00003.clpi" yEnc (1/1) 480',
        '[31/141] - "00004.clpi" yEnc (1/1) 1136',
        '[32/141] - "00005.clpi" yEnc (1/1) 480',
        '[33/141] - "00006.clpi" yEnc (1/1) 480',
        '[34/141] - "00007.clpi" yEnc (1/1) 712',
        '[35/141] - "00008.clpi" yEnc (1/1) 392',
        '[36/141] - "00009.clpi" yEnc (1/1) 1016',
        '[37/141] - "00010.clpi" yEnc (1/1) 1000',
        '[38/141] - "00011.clpi" yEnc (1/1) 296',
        '[39/141] - "00012.clpi" yEnc (1/1) 296',
        '[40/141] - "00013.clpi" yEnc (1/1) 332',
        '[41/141] - "00014.clpi" yEnc (1/1) 332',
        '[42/141] - "bdmt_jpn.xml" yEnc (1/1) 446',
        '[43/141] - "fafner_BTL_L_xmb.jpg" yEnc (1/1) 267785',
        '[44/141] - "fafner_BTL_S_xmb.jpg" yEnc (1/1) 137371',
        '[45/141] - "MovieObject.bdmv" yEnc (1/1) 39430',
        '[46/141] - "00001.mpls" yEnc (1/1) 708',
        '[47/141] - "00002.mpls" yEnc (1/1) 188',
        '[48/141] - "00003.mpls" yEnc (1/1) 188',
        '[49/141] - "00004.mpls" yEnc (1/1) 188',
        '[50/141] - "00005.mpls" yEnc (1/1) 188',
        '[51/141] - "00006.mpls" yEnc (1/1) 188',
        '[52/141] - "00007.mpls" yEnc (1/1) 188',
        '[53/141] - "00008.mpls" yEnc (1/1) 174',
        '[54/141] - "00009.mpls" yEnc (1/1) 13046',
        '[55/141] - "00010.mpls" yEnc (1/1) 158',
        '[56/141] - "00011.mpls" yEnc (1/1) 158',
        '[57/141] - "00001.m2ts" yEnc (1/23594) 16911587328',
        '[58/141] - "00002.m2ts" yEnc (1/378) 270790656',
        '[59/141] - "00003.m2ts" yEnc (1/99) 70281216',
        '[60/141] - "00004.m2ts" yEnc (1/649) 464873472',
        '[61/141] - "00005.m2ts" yEnc (1/101) 71995392',
        '[62/141] - "00006.m2ts" yEnc (1/101) 71995392',
        '[63/141] - "00007.m2ts" yEnc (1/240) 171515904',
        '[64/141] - "00008.m2ts" yEnc (1/11) 7606272',
        '[65/141] - "00009.m2ts" yEnc (1/308) 220569600',
        '[66/141] - "00010.m2ts" yEnc (1/281) 201308160',
        '[67/141] - "00011.m2ts" yEnc (1/13) 8742912',
        '[68/141] - "00012.m2ts" yEnc (1/3) 2033664',
        '[69/141] - "00013.m2ts" yEnc (1/2) 1062912',
        '[70/141] - "00014.m2ts" yEnc (1/1) 110592',
        '[71/141] - "index.bdmv" yEnc (1/1) 280',
    ]
    randomized = random.sample(control, len(control))
    assert sorted(randomized, key=sort_key_from_subject) == control
