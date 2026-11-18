#!/usr/bin/env python3
"""Gate check for the cam edge clamp example, using aiascam.verify.

Re-reads the emitted .nc files from disk and replays them on a simulated blank: generic gates
(comments, feeds vs machine.yaml limits, rapids, plunges, outside blank, air audit) plus part
checks (no gouge, nut pocket flat, holes and cutout through).
Usage: python3 check_cam.py [out_dir]   (CONFIG env var: same config dir the generator used)
"""
import json
import os
import sys

from shapely import contains_xy
from shapely.geometry import Point

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from aiascam.config import feed_limits  # noqa: E402
from aiascam.verify import Stock, run_file, part  # noqa: E402
import cam_geom as G  # noqa: E402
import gen_cam as GC  # noqa: E402


def main():
    D = sys.argv[1] if len(sys.argv) > 1 else GC.OUT
    info = json.load(open(os.path.join(D, "gen-info.json")))
    zt = info["z_through"]
    limits = feed_limits(GC.MACH)
    s = Stock(*info["blank"])
    fails = []
    for f, d in [("cam-0-TRACE-spindle-off.nc", GC.T2_D), ("cam-1-T1-nut-pocket.nc", GC.T1_D),
                 ("cam-2-T2-TEST-plug.nc", GC.T2_D), ("cam-3-T2-holes-cutout.nc", GC.T2_D)]:
        r = run_file(os.path.join(D, f), s, d, limits)
        print(f"{f}: feed {r['feed_mm'] / 1000:.2f} m, air {r['air_pct']:.0f} %")
        fails += [f"{f}: {x}" for x in r["fails"]]
    X, Y = s.grid()
    P = GC.part_polygon(); pk = GC.pocket_region(); dcx, dcy = GC.drive_c()
    inside = contains_xy(P.buffer(-(GC.CLEAN + 0.1)), X, Y)
    piv = contains_xy(Point(0, 0).buffer(G.PIVOT_D / 2 + 0.08), X, Y)
    drv = contains_xy(Point(dcx, dcy).buffer(G.DRIVE_D / 2 + 0.08), X, Y)
    pkt = contains_xy(pk.buffer(0.08), X, Y)
    fails += part.untouched(s, inside & ~piv & ~drv & ~pkt, "part")
    fails += part.at_depth(s, contains_xy(pk.buffer(-0.12), X, Y) & ~drv, -G.NUT_DEPTH, "nut pocket")
    fails += part.through(s, contains_xy(Point(0, 0).buffer(G.PIVOT_D / 2 - 0.1), X, Y), zt, "pivot hole")
    fails += part.through(s, contains_xy(Point(dcx, dcy).buffer(G.DRIVE_D / 2 - 0.1), X, Y), zt, "drive hole")
    ring = contains_xy(P.buffer(0.15), X, Y) & ~contains_xy(P.buffer(0.05), X, Y)
    fails += part.through(s, ring, zt, "cutout")
    if fails:
        print("FAIL")
        for f in fails[:40]:
            print("  " + f)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
