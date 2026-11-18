import os
import tempfile
from aiascam.verify import Stock, run_file, part


def _nc(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".nc", delete=False)
    f.write(text)
    f.close()
    return f.name


GOOD = """(good: ramp in, cut a line, retract)
G21 G90
G0 Z5
G0 X2 Y5
G1 Z0 F300
G1 X8 Y5 Z-0.5 F300
G1 X18 Y5 F500
G0 Z5
"""

BAD = """(bad (nested) comment)
G0 Z5
G0 X5 Y5
G1 Z-1 F300
G0 X15 Y5
G1 X18 F2000
G1 X19
"""


def test_good_passes():
    s = Stock(0, 0, 20, 10)
    r = run_file(_nc(GOOD), s, 3.175, {"feed_xy": 1000, "feed_z": 500})
    assert r["fails"] == [], r["fails"]
    assert r["air_pct"] < 50


def test_bad_fails_every_gate():
    s = Stock(0, 0, 20, 10)
    r = run_file(_nc(BAD), s, 3.175, {"feed_xy": 1000})
    txt = "\n".join(r["fails"])
    for key in ("comment", "PLUNGE", "RAPID", "over limit"):
        assert key in txt, (key, txt)


def test_no_limits_skips_feed_gate():
    s = Stock(0, 0, 20, 10)
    r = run_file(_nc(BAD), s, 3.175)
    assert not any("over limit" in f for f in r["fails"])


def test_part_checks():
    s = Stock(0, 0, 20, 10)
    run_file(_nc(GOOD), s, 3.175)
    X, Y = s.grid()
    assert part.untouched(s, Y > 8) == []
    assert part.untouched(s, (Y > 4) & (Y < 6) & (X > 12))
    assert part.at_depth(s, (abs(Y - 5) < 1) & (X > 10) & (X < 17), -0.5) == []
