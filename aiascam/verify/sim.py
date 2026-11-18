"""Replay G-code on a height-map block of stock and run the gates.

Gates (each a list of failures):
  comments   malformed / nested comment brackets
  no_feed    feed move with no F word
  feed_limit F over the machine's limit (only if limits are configured)
  rapid      G0 touches stock
  plunge     straight G1 descent into material (helix/ramp required)
  outside    cutting below Z0 outside the blank
Air audit: feed travel that removes nothing, per file and per tenth of the file.
Tool model: flat end mill (cylinder). Stock top is Z0.
"""
import math
import numpy as np
from ..gcode import parse


class Stock:
    def __init__(self, x0, y0, x1, y1, res=0.1):
        self.x0, self.y0, self.res = x0, y0, res
        self.nx = int(round((x1 - x0) / res)) + 1
        self.ny = int(round((y1 - y0) / res)) + 1
        self.h = np.zeros((self.ny, self.nx))
        self.xs = x0 + np.arange(self.nx) * res
        self.ys = y0 + np.arange(self.ny) * res

    def grid(self):
        return np.meshgrid(self.xs, self.ys)


def _disk(r, res):
    n = int(math.ceil(r / res))
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1]
    return n, (xx * res) ** 2 + (yy * res) ** 2 <= r * r


def _samples(m, step=0.05):
    a, b = m["a"], m["b"]
    if m["mode"] in (0, 1):
        L = math.dist((a["X"], a["Y"], a["Z"]), (b["X"], b["Y"], b["Z"]))
        t = np.linspace(0, 1, max(1, int(L / step)) + 1)
        xy = math.hypot(b["X"] - a["X"], b["Y"] - a["Y"])
        return (a["X"] + (b["X"] - a["X"]) * t, a["Y"] + (b["Y"] - a["Y"]) * t,
                a["Z"] + (b["Z"] - a["Z"]) * t, xy, L)
    cx, cy = a["X"] + m["i"], a["Y"] + m["j"]
    r = math.hypot(m["i"], m["j"])
    a0 = math.atan2(a["Y"] - cy, a["X"] - cx)
    a1 = math.atan2(b["Y"] - cy, b["X"] - cx)
    if m["mode"] == 3:
        while a1 <= a0 + 1e-9:
            a1 += 2 * math.pi
    else:
        while a1 >= a0 - 1e-9:
            a1 -= 2 * math.pi
    arc = abs(a1 - a0) * r
    t = np.linspace(0, 1, max(2, int(arc / step)) + 1)
    ang = a0 + (a1 - a0) * t
    return (cx + r * np.cos(ang), cy + r * np.sin(ang), a["Z"] + (b["Z"] - a["Z"]) * t,
            arc, math.hypot(arc, b["Z"] - a["Z"]))


def run_file(path, stock, tool_d, limits=None, plunge_ratio=0.25):
    """Replay one file on `stock` (modified in place). Returns a report dict.

    limits: optional dict, e.g. {"feed_xy": 750, "feed_z": 600}. Missing keys skip that check.
    """
    limits = limits or {}
    moves, issues = parse(path)
    fails = [f"line {n}: {msg}" for n, msg in issues]
    n, mask = _disk(tool_d / 2, stock.res)
    last = max((m["line"] for m in moves), default=1)
    feed_len = air_len = 0.0
    tenths = [[0.0, 0.0] for _ in range(10)]
    for m in moves:
        ln = m["line"]
        a, b = m["a"], m["b"]
        if m["mode"] != 0:
            if m["f"] is None:
                fails.append(f"line {ln}: feed move with no F")
            else:
                zonly = abs(b["X"] - a["X"]) < 1e-9 and abs(b["Y"] - a["Y"]) < 1e-9
                lim = limits.get("feed_z" if zonly else "feed_xy")
                if lim is not None and m["f"] > lim + 1e-6:
                    fails.append(f"line {ln}: F{m['f']:g} over limit {lim:g}")
        xs, ys, zs, xy_len, L = _samples(m)
        removed = False
        for x, y, z in zip(xs, ys, zs):
            ix = int(round((x - stock.x0) / stock.res))
            iy = int(round((y - stock.y0) / stock.res))
            x0, x1, y0, y1 = ix - n, ix + n + 1, iy - n, iy + n + 1
            if x0 < 0 or y0 < 0 or x1 > stock.nx or y1 > stock.ny:
                if z < 0:
                    fails.append(f"line {ln}: cuts outside the blank at X{x:.2f} Y{y:.2f}")
                continue
            win = stock.h[y0:y1, x0:x1]
            hit = mask & (win > z + 1e-6)
            if hit.any():
                if m["mode"] == 0:
                    fails.append(f"line {ln}: RAPID into stock at X{x:.2f} Y{y:.2f} Z{z:.3f}")
                removed = True
                win[hit] = z
        if m["mode"] != 0:
            dz = a["Z"] - b["Z"]
            if removed and m["mode"] == 1 and dz > 0.05 and xy_len < plunge_ratio * dz:
                fails.append(f"line {ln}: straight PLUNGE into material, dz {dz:.3f} over {xy_len:.3f}")
            feed_len += L
            k = min(9, int(10 * (ln - 1) / last))
            tenths[k][0] += L
            if not removed:
                air_len += L
                tenths[k][1] += L
    return dict(file=path, fails=fails, feed_mm=feed_len, air_mm=air_len,
                air_pct=100 * air_len / feed_len if feed_len else 0.0,
                air_tenths=[100 * a / t if t else None for t, a in tenths])
