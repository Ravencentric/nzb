## Parsing an NZB

```py
from nzb import Nzb

text = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
    <head>
        <meta type="title">Big Buck Bunny - S01E01.mkv</meta>
        <meta type="password">secret</meta>
        <meta type="tag">HD</meta>
        <meta type="category">TV</meta>
    </head>
    <file poster="John &lt;nzb@nowhere.example&gt;" date="1706440708" subject="[1/1] - &quot;Big Buck Bunny - S01E01.mkv&quot; yEnc (1/2) 1478616">
        <groups>
            <group>alt.binaries.boneless</group>
        </groups>
        <segments>
            <segment bytes="739067" number="1">9cacde4c986547369becbf97003fb2c5-9483514693959@example</segment>
            <segment bytes="739549" number="2">70a3a038ce324e618e2751e063d6a036-7285710986748@example</segment>
        </segments>
    </file>
</nzb>
"""

nzb = Nzb.from_str(text)
# Alternatively, we can also parse an nzb file directly:
# nzb = Nzb.from_file("big_buck_bunny.nzb")

print(f"{nzb.file.name} ({nzb.meta.category}) was posted by {nzb.file.poster} on {nzb.file.posted_at}.")
print(f"Number of files: {len(nzb.files)}")
print(f"Total size in bytes: {nzb.size}")
```

## JSON round-tripping

We can also serialize to JSON and deserialize from JSON.

```py
from nzb import Nzb

text = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.1//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.1.dtd">
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
    <head>
        <meta type="title">Big Buck Bunny - S01E01.mkv</meta>
        <meta type="password">secret</meta>
        <meta type="tag">HD</meta>
        <meta type="category">TV</meta>
    </head>
    <file poster="John &lt;nzb@nowhere.example&gt;" date="1706440708" subject="[1/1] - &quot;Big Buck Bunny - S01E01.mkv&quot; yEnc (1/2) 1478616">
        <groups>
            <group>alt.binaries.boneless</group>
        </groups>
        <segments>
            <segment bytes="739067" number="1">9cacde4c986547369becbf97003fb2c5-9483514693959@example</segment>
            <segment bytes="739549" number="2">70a3a038ce324e618e2751e063d6a036-7285710986748@example</segment>
        </segments>
    </file>
</nzb>
"""

original = Nzb.from_str(text)
serialized = original.to_json()
deserialized = Nzb.from_json(serialized)

assert original == deserialized # True
```
If you're curious, this is what the resulting JSON looks like:

```json
{
  "meta": {
    "title": "Big Buck Bunny - S01E01.mkv",
    "passwords": ["secret"],
    "tags": ["HD"],
    "category": "TV"
  },
  "files": [
    {
      "poster": "John <nzb@nowhere.example>",
      "posted_at": "2024-01-28T11:18:28Z",
      "subject": "[1/1] - \"Big Buck Bunny - S01E01.mkv\" yEnc (1/2) 1478616",
      "groups": ["alt.binaries.boneless"],
      "segments": [
        {
          "size": 739067,
          "number": 1,
          "message_id": "9cacde4c986547369becbf97003fb2c5-9483514693959@example"
        },
        {
          "size": 739549,
          "number": 2,
          "message_id": "70a3a038ce324e618e2751e063d6a036-7285710986748@example"
        }
      ]
    }
  ]
}
```

## NZB Meta Editor