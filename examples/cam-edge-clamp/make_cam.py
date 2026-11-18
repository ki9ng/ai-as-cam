#!/usr/bin/env python3
"""Spiral cam edge clamp v4 — CadQuery model (geometry lives in cam_geom.py).

The cam turns on an M6 pivot bolt into the T-nut / grid hole. Off-centre, an M5 x 12 SHCS
goes down through the drive hole into an M5 nut held in a hex pocket in the cam's BOTTOM;
tightened once, that bolt is part of the cam, so a 4 mm hex key in it turns the cam about
the pivot. Clockwise swings the spiral out to the part; hold it with the key and tighten
the pivot bolt.
v4 no counterbores — both heads sit on top — so it is ONE setup:
blank glued bottom-up, nut pocket + holes + cutout.
History: v1 round lever hole (key spins in it); v2 captive nut on the pivot (wrong hole);
v3 counterbored heads, two setups.

Run: python make_cam.py && python draw_cam.py
"""
import math, os
import cadquery as cq
from cam_geom import *          # noqa: F401,F403  (parameters + outline + drive_xy)
import cam_geom as G

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def nut_pocket():
    dx, dy = G.drive_xy()
    cut = cq.Workplane("XY").polyline(G.hex_pts(dx, dy)).close().extrude(G.NUT_DEPTH)
    for cx, cy in G.relief_centres(dx, dy):
        cut = cut.union(cq.Workplane("XY").center(cx, cy).circle(G.RELIEF_D / 2).extrude(G.NUT_DEPTH))
    return cut


def cam_solid():
    s = cq.Workplane("XY").polyline(G.outline()).close().extrude(G.H)
    th = G.TH
    s = s.edges(cq.selectors.NearestToPointSelector((G.R0 * math.cos(th), G.R0 * math.sin(th), G.H / 2))).fillet(G.R_STEP)
    s = s.edges(cq.selectors.NearestToPointSelector((G.R_MAX * math.cos(th), G.R_MAX * math.sin(th), G.H / 2))).fillet(G.R_TIP)
    piv = cq.Workplane("XY").circle(G.PIVOT_D / 2).extrude(G.H)
    dx, dy = G.drive_xy()
    drv = cq.Workplane("XY").center(dx, dy).circle(G.DRIVE_D / 2).extrude(G.H)
    return s.cut(piv).cut(drv).cut(nut_pocket())


def numbers():
    return G.numbers()


def main():
    os.makedirs(OUT, exist_ok=True)
    c = cam_solid()
    cq.exporters.export(c, f"{OUT}/cam.step")
    cq.exporters.export(c, f"{OUT}/cam.stl")
    cq.exporters.export(c.section(G.H - 0.01), f"{OUT}/cam-top.dxf", exportType="DXF")
    cq.exporters.export(c.section(0.01), f"{OUT}/cam-bottom.dxf", exportType="DXF")
    n = G.numbers()
    assert n["slope_deg_at_R0"] < n["self_lock_limit_deg"], "spiral too steep to self-lock"
    for k in ("drive_hole_to_pivot_hole", "nut_pocket_to_pivot_hole", "nut_pocket_to_edge"):
        assert n[k] > 1.2, f"{k} too thin: {n[k]:.2f}"
    assert n["nut_engagement_with_m5x12"] >= 3.0, "M5 x 12 doesn't reach far enough into the nut"
    for k, v in n.items():
        print(f"  {k}: {v:.3f}")
    bb = c.val().BoundingBox()
    print(f"bbox {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f}; mass 6061 {c.val().Volume()*2.7e-3:.1f} g")


if __name__ == "__main__":
    main()
