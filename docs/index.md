<br/>
<p align="center">
  <a href="https://github.com/Ravencentric/nzb">
    <img src="https://raw.githubusercontent.com/Ravencentric/nzb/main/docs/assets/logo.png" alt="Logo" width="200">
  </a>
  <p align="center">
    A spec compliant parser and meta editor for NZB files
    <br/>
    <br/>
  </p>
</p>

<p align="center">
<a href="https://pypi.org/project/nzb/"><img src="https://img.shields.io/pypi/v/nzb" alt="PyPI - Version" ></a>
<img src="https://img.shields.io/pypi/pyversions/nzb" alt="PyPI - Python Version">
<img src="https://img.shields.io/github/license/Ravencentric/nzb" alt="License">
<img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
</p>

<p align="center">
<img src="https://img.shields.io/github/actions/workflow/status/Ravencentric/nzb/release.yml?" alt="GitHub Workflow Status">
<img src="https://img.shields.io/github/actions/workflow/status/Ravencentric/nzb/test.yml?label=tests" alt="GitHub Workflow Status">
<a href="https://codecov.io/gh/Ravencentric/nzb"><img src="https://codecov.io/gh/Ravencentric/nzb/graph/badge.svg?token=FFSOFFOM6J" alt="Codecov"></a>
</p>


## About

A [spec](https://sabnzbd.org/wiki/extra/nzb-spec) compliant parser and meta editor for NZB files.

## Installation

`nzb` is available on [PyPI](https://pypi.org/project/nzb/), so you can simply use [pip](https://github.com/pypa/pip) to install it.

```sh
pip install nzb
```

## Usage

```py
from nzb import NZBParser

nzb = NZBParser.from_file("Big Buck Bunny - S01E01.mkv.nzb").parse()

print(f"{nzb.file.name} ({nzb.file.size.human_readable()})")
#> Big Buck Bunny - S01E01.mkv (16.7MiB)

for file in nzb.files:
    print((file.name, file.size, file.datetime.isoformat(), file.groups))
    #> ("Big Buck Bunny - S01E01.mkv", 17521761, "2024-01-28T11:18:28+00:00", ("alt.binaries.boneless",))
    #> ("Big Buck Bunny - S01E01.mkv.par2", 1089, "2024-01-28T11:18:29+00:00", ("alt.binaries.boneless",))
    #> ("Big Buck Bunny - S01E01.mkv.vol00+01.par2", 741017, "2024-01-28T11:18:29+00:00", ("alt.binaries.boneless",))
    #> ("Big Buck Bunny - S01E01.mkv.vol01+02.par2", 1480494, "2024-01-28T11:18:29+00:00", ("alt.binaries.boneless",))
    #> ("Big Buck Bunny - S01E01.mkv.vol03+04.par2", 2960528, "2024-01-28T11:18:29+00:00", ("alt.binaries.boneless",))
```

## License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License. See [LICENSE](https://github.com/Ravencentric/nzb/blob/main/LICENSE) for more information.
