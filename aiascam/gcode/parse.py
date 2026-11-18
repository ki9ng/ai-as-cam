"""Parse G-code from disk into motion moves. Never trust the generator's in-memory copy."""
import re

WORD = re.compile(r"([A-Z])\s*([-+]?[0-9]*\.?[0-9]+)")


def parse(path, start=(0.0, 0.0, 5.0)):
    """Return (moves, issues).

    moves: list of dicts {line, mode (0-3), a (start xyz dict), b (end xyz dict), i, j, f}
    issues: list of (line, message) for malformed comments.
    Handles G0-G3 in XY plane, absolute mm. Other modal codes are ignored.
    """
    pos = dict(X=start[0], Y=start[1], Z=start[2])
    mode, feed = 0, None
    moves, issues = [], []
    with open(path) as fh:
        lines = fh.read().splitlines()
    for n, raw in enumerate(lines, 1):
        line = raw.strip().upper()
        if line.count("(") != line.count(")") or line.count("(") > 1:
            issues.append((n, f"comment brackets: {raw.strip()}"))
        line = re.sub(r"\(.*?\)", "", line).split(";")[0].strip()
        if not line:
            continue
        words = {}
        gs = []
        for k, v in WORD.findall(line):
            if k == "G":
                gs.append(float(v))
            else:
                words[k] = float(v)
        motion = [g for g in gs if g in (0, 1, 2, 3)]
        if motion:
            mode = int(motion[-1])
        if "F" in words:
            feed = words["F"]
        if not any(k in words for k in "XYZ"):
            continue
        if gs and not motion:
            continue                      # e.g. G92/G10 with coordinates: not a move
        new = dict(pos)
        for k in "XYZ":
            if k in words:
                new[k] = words[k]
        moves.append(dict(line=n, mode=mode, a=dict(pos), b=new,
                          i=words.get("I", 0.0), j=words.get("J", 0.0), f=feed))
        pos = new
    return moves, issues
