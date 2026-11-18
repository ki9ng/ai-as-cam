#!/usr/bin/env python3
"""EXAMPLE. Every feed, speed and depth is read from config/ (machine.yaml, tools.yaml).
The shipped config is one 3018-class machine: set CONFIG to your own before generating.

Spiral cam edge clamp v4 — G-code, ONE setup (blank glued BOTTOM-UP).

  cam-0-TRACE-spindle-off.nc   any tool, spindle OFF: traces the outer edge of every kerf at Z+2
  cam-1-T1-nut-pocket.nc      T1 1.5 mm O-flute: M5 nut pocket 8.1 AF x 4.2 + corner reliefs
  -- tool change -> T2 1/8 in DLC single flute, re-zero Z ONLY at the touch-off point --
  cam-2-T2-TEST-plug.nc       T2 FIRST USE IN ALUMINIUM: trochoidal kerf round a 6 x 6 plug,
                               full depth, same settings as the cutout. Measure, then go on.
  cam-3-T2-holes-cutout.nc    T2: pivot 6.6 + drive 5.5 helix bores, trochoidal cutout, spring +
                               cleanup pass. LAST.
  cam-3b-T2-cleanup.nc        T2: stand-alone 0.05 wall cleanup, if the edge needs it.

Zero: X0 Y0 = PIVOT CENTRE (cam seen from its bottom, i.e. as it lies on the bed), Z0 = top of
the stock. House rules (see docs/agent/CLAUDE.md): never plunge (helix / ramp everything), T1 slotting is
trochoidal, never a full-width slot, CCW front arc = the cut, feeds within the machine.yaml limits, comments
never nest, cutoff last, one tool change.

Env: CONFIG (config dir), STOCK (default from machine.yaml job — CALIPER IT), T2_D (default 3.175 — replace with the plug-test value),
DOC_T2 (cutout depth per level, default ~1 x D), OUT (default ./out).
"""
import math, os, sys
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import cam_geom as G

# ---- all machine and tool numbers come from config (machine.yaml / tools.yaml) ----
# Point CONFIG at your own folder; the shipped config/ is ONE example machine, not safe defaults.
import yaml
CFG = os.environ.get("CONFIG", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
MACH = yaml.safe_load(open(os.path.join(CFG, "machine.yaml")))
TOOLS = {t["id"]: t for t in yaml.safe_load(open(os.path.join(CFG, "tools.yaml")))["tools"]}
JOB = MACH.get("job", {})
T1, T2 = TOOLS[JOB.get("pocket_tool", "T1")], TOOLS[JOB.get("cutout_tool", "T2")]

STOCK = float(os.environ.get("STOCK", JOB.get("stock_mm", 12.7)))   # CALIPER IT
BREAK = JOB.get("break_through_mm", 0.20)                            # into the glue
ZT = -(STOCK + BREAK)
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
ZSAFE = MACH.get("z_safe_mm", 3.0)
S = MACH.get("spindle_rpm", {}).get("default", 10000)

# ---- T1: pocket tool ----
T1_D = T1["diameter_mm"]
P = T1["pocket"]
P_DOC, P_STEP, P_F, P_FZ = P["doc_mm"], P["stepover_mm"], P["feed"], P["helix_feed"]
P_HELIX_R, P_HELIX_PITCH = P["helix_r_mm"], P["helix_pitch_mm"]

# ---- T2: cutout tool, trochoidal ----
T2_D = float(os.environ.get("T2_D", T2["diameter_mm"]))   # replace with the measured cut dia
TR = T2["trochoid"]
LOOP_R = TR["loop_r_mm"]         # kerf = D + 2 * LOOP_R
W = T2_D + 2 * LOOP_R
STEP = TR["step_mm"]
F_CUT, F_AIR, F_HELIX, F_FIN, FZ = TR["feed"], TR["air_feed"], TR["helix_feed"], TR["finish_feed"], TR["z_feed"]
HELIX_PITCH = TR["helix_pitch_mm"]
CLEAN = TR["cleanup_mm"]
DOC_T2 = float(os.environ.get("DOC_T2", TR.get("doc_mm", 0)))   # 0 -> ~1 x D, evenly split
HOLE_F, HOLE_PITCH = T2["bore"]["feed"], T2["bore"]["helix_pitch_mm"]

TOUCH_NOTE = "touch-off point"


def safe(s):
    s = s.replace("(", "[").replace(")", "]")
    return f"({s})"


def f3(v):
    return f"{v:.3f}"


def mir(p):
    return (-p[0], p[1])


# ---------------------------------------------------------------- geometry in the MACHINE frame
def part_polygon():
    P = Polygon([mir(p) for p in G.outline()])
    P = P.buffer(G.R_STEP, resolution=64).buffer(-G.R_STEP, resolution=64)       # concave step fillet
    P = P.buffer(-G.R_TIP, resolution=64).buffer(G.R_TIP, resolution=64)         # round the tip
    return P


def drive_c():
    return mir(G.drive_xy())


def pocket_region():
    cx, cy = drive_c()
    hexp = Polygon(G.hex_pts(cx, cy))
    rel = [Point(p).buffer(G.RELIEF_D / 2, resolution=32) for p in G.relief_centres(cx, cy)]
    return unary_union([hexp] + rel)


def test_plug(P):
    """6 x 6 plug in the waste left of the cam's kerf."""
    minx = P.buffer(W).bounds[0]
    x1 = minx - 4.0 - W
    return Polygon([(x1 - 6, -3), (x1, -3), (x1, 3), (x1 - 6, 3)])


# ---------------------------------------------------------------- trochoidal kerf round a polygon
def troch(P, levels, label):
    """Port of usmc-keychain/troch.py for a given tool. Returns (lines, minutes, info)."""
    Dt = T2_D
    CL = P.buffer(W / 2, resolution=64).buffer(0.4, resolution=32).buffer(-0.4, resolution=32)
    ring = np.array(CL.exterior.coords)
    if not Polygon(ring).exterior.is_ccw:
        ring = ring[::-1]
    seg = np.linalg.norm(np.diff(ring, axis=0), axis=1)
    s_ = np.concatenate([[0], np.cumsum(seg)]); per = s_[-1]
    ss = np.arange(0, per, 0.01)
    X = np.interp(ss, s_, ring[:, 0]); Y = np.interp(ss, s_, ring[:, 1])
    dx = np.gradient(np.r_[X[-3:], X, X[:3]])[3:-3]; dy = np.gradient(np.r_[Y[-3:], Y, Y[:3]])[3:-3]
    nrm = np.hypot(dx, dy); tx, ty = dx / nrm, dy / nrm
    nRx, nRy = ty, -tx                                   # right normal = away from the part
    R = LOOP_R
    ri, ro = R + Dt / 2, -(R + Dt / 2)
    idx = [0]
    for i in range(1, len(ss)):
        j = idx[-1]
        for o in (ri, ro):
            if math.hypot(X[i] + o * nRx[i] - X[j] - o * nRx[j], Y[i] + o * nRy[i] - Y[j] - o * nRy[j]) >= STEP:
                idx.append(i); break
    idx.append(0)
    mind = min(P.exterior.distance(Point(X[i], Y[i])) for i in idx[::5])
    assert mind >= W / 2 - 0.01, f"loop centre only {mind:.3f} from the part"
    L, t = [], 0.0
    x0, y0 = X[0] + R * nRx[0], Y[0] + R * nRy[0]
    zprev = 0.0
    L.append(safe(f"{label}: TROCHOIDAL KERF {W:.3f} wide, loop r {R}, step {STEP}, centreline {per:.1f} mm, "
                  f"{len(idx) - 1} loops/level, {len(levels)} levels to Z{levels[-1]:.3f}"))
    for li, z in enumerate(levels):
        L.append(safe(f"{label} LEVEL {li + 1} Z{z:.3f}"))
        L += [f"G0 Z{ZSAFE:.3f}" if li == 0 else "G0 Z0.500", f"G0 X{f3(x0)} Y{f3(y0)}",
              f"G0 Z{f3(zprev + 0.3)}", f"G1 Z{f3(zprev)} F{FZ}"]
        I, J = -R * nRx[0], -R * nRy[0]
        turns = max(1, int(math.ceil((zprev - z) / HELIX_PITCH - 1e-9)))
        for k in range(1, turns + 1):
            L.append(f"G3 X{f3(x0)} Y{f3(y0)} Z{f3(zprev - (zprev - z) * k / turns)} I{f3(I)} J{f3(J)} F{F_HELIX}")
            t += 2 * math.pi * R / F_HELIX
        L.append(f"G3 X{f3(x0)} Y{f3(y0)} I{f3(I)} J{f3(J)} F{F_CUT}"); t += 2 * math.pi * R / F_CUT
        for a, b in zip(idx[:-1], idx[1:]):
            fa = (X[a] - R * nRx[a], Y[a] - R * nRy[a])
            L.append(f"G3 X{f3(fa[0])} Y{f3(fa[1])} I{f3(-R * nRx[a])} J{f3(-R * nRy[a])} F{F_CUT}")
            t += math.pi * R / F_CUT
            nb = (X[b] + R * nRx[b], Y[b] + R * nRy[b])
            mx, my = (fa[0] + nb[0]) / 2, (fa[1] + nb[1]) / 2
            L.append(f"G3 X{f3(nb[0])} Y{f3(nb[1])} I{f3(mx - fa[0])} J{f3(my - fa[1])} F{F_AIR}")
            t += math.pi * math.hypot(nb[0] - fa[0], nb[1] - fa[1]) / 2 / F_AIR
        L.append(f"G3 X{f3(x0)} Y{f3(y0)} I{f3(I)} J{f3(J)} F{F_CUT}"); t += 2 * math.pi * R / F_CUT
        zprev = z
    zt = levels[-1]
    fin = np.array(P.buffer(Dt / 2, resolution=64).exterior.simplify(0.005).coords)
    if Polygon(fin).exterior.is_ccw:
        fin = fin[::-1]
    k0 = int(np.argmin([math.dist(q, (X[0], Y[0])) for q in fin])); fin = np.r_[fin[k0:-1], fin[:k0 + 1]]
    L.append(safe(f"{label} SPRING PASS - part wall at Z{zt:.3f}, CW, F{F_FIN}"))
    L += [f"G1 X{f3(fin[0][0])} Y{f3(fin[0][1])} Z{f3(zt)} F{F_FIN}"] + [f"G1 X{f3(q[0])} Y{f3(q[1])}" for q in fin[1:]]
    t += float(np.sum(np.linalg.norm(np.diff(fin, axis=0), axis=1))) / F_FIN
    cl = np.array(P.buffer(Dt / 2 - CLEAN, resolution=64).exterior.simplify(0.005).coords)
    if Polygon(cl).exterior.is_ccw:
        cl = cl[::-1]
    k = int(np.argmin([math.dist(q, (X[0], Y[0])) for q in cl])); cl = np.r_[cl[k:-1], cl[:k + 1]]
    ex, ey = cl[0][0] + 0.6 * nRx[0], cl[0][1] + 0.6 * nRy[0]
    assert P.exterior.distance(Point(ex, ey)) > Dt / 2 + 0.05
    clen = float(np.sum(np.linalg.norm(np.diff(cl, axis=0), axis=1)))
    CB = [safe(f"{label} CLEANUP PASS - {CLEAN:.2f} mm off the part wall, Z{zt:.3f}, CW, F{F_FIN}, lead-in from the kerf"),
          f"G0 Z{ZSAFE:.3f}", f"G0 X{f3(ex)} Y{f3(ey)}", "G0 Z0.500", f"G1 Z{f3(zt)} F{FZ}",
          f"G1 X{f3(cl[0][0])} Y{f3(cl[0][1])} F{F_FIN}"] + [f"G1 X{f3(q[0])} Y{f3(q[1])}" for q in cl[1:]] + \
         [f"G1 X{f3(ex)} Y{f3(ey)}"]
    ct = clen / F_FIN + 1.2 / F_FIN + (-zt + 0.5) / FZ
    L += CB; t += ct
    return L, t, CB, ct, dict(centreline=per, loops=len(idx) - 1, min_centre_to_part=mind)


def helix_bore(cx, cy, d, z_from, z_to, label):
    r = d / 2 - T2_D / 2
    assert r > 0.2, f"{label}: hole {d} too small for the {T2_D} tool"
    sx, sy = cx + r, cy
    L = [safe(f"{label}: {d:.2f} bore, helix r {r:.3f}, {HOLE_PITCH}/rev F{HOLE_F}, Z{z_from:.3f} -> Z{z_to:.3f}"),
         f"G0 Z{ZSAFE:.3f}", f"G0 X{f3(sx)} Y{f3(sy)}", f"G0 Z{f3(z_from + 0.5)}", f"G1 Z{f3(z_from)} F{FZ}"]
    turns = int(math.ceil((z_from - z_to) / HOLE_PITCH - 1e-9))
    for k in range(1, turns + 1):
        L.append(f"G3 X{f3(sx)} Y{f3(sy)} Z{f3(z_from - (z_from - z_to) * k / turns)} I{f3(-r)} J0.000 F{HOLE_F}")
    L += [f"G3 X{f3(sx)} Y{f3(sy)} I{f3(-r)} J0.000 F{HOLE_F}", f"G1 X{f3(cx)} Y{f3(cy)} F{HOLE_F}",
          f"G0 Z{ZSAFE:.3f}"]
    t = (turns + 1) * 2 * math.pi * r / HOLE_F + 0.5 / FZ
    return L, t


def nut_pocket():
    """T1: helix bore at the drive centre to full pocket depth, then per level, rings inside-out
    (CCW = climb), each ring a stepover wider — no ring ever cuts a full-width slot."""
    cx, cy = drive_c()
    reg = pocket_region()
    rc = reg.buffer(-T1_D / 2, resolution=64)
    rings = []
    d = 0.0
    while True:
        g = rc.buffer(-d, resolution=64)
        if g.is_empty or g.area < 1e-3:
            break
        polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        for pg in polys:
            c = np.array(pg.exterior.simplify(0.003).coords)
            if not Polygon(c).exterior.is_ccw:
                c = c[::-1]
            rings.append((d, c))
        d += P_STEP
    rings.sort(key=lambda r: -r[0])              # innermost first
    bore_r = P_HELIX_R + T1_D / 2
    # every ring must be within one stepover of the previous cut (inner bore for the first)
    zt = -G.NUT_DEPTH
    n = int(math.ceil(G.NUT_DEPTH / P_DOC - 1e-9)); levels = [round(zt * k / n, 4) for k in range(1, n + 1)]
    L = [safe(f"NUT POCKET: {G.NUT_AF} AF x {G.NUT_DEPTH} + 6 x {G.RELIEF_D} corner reliefs at the drive hole "
              f"X{cx:.3f} Y{cy:.3f}"),
         safe(f"helix bore r {P_HELIX_R} to Z{zt:.3f} at {P_HELIX_PITCH}/rev F{P_FZ}, then {len(levels)} levels of "
              f"{G.NUT_DEPTH / n:.3f}, {len(rings)} rings inside-out at {P_STEP} stepover, F{P_F}"),
         f"G0 Z{ZSAFE:.3f}", f"G0 X{f3(cx + P_HELIX_R)} Y{f3(cy)}", "G0 Z0.500", f"G1 Z0.000 F{P_FZ}"]
    t = 0.0
    turns = int(math.ceil(G.NUT_DEPTH / P_HELIX_PITCH - 1e-9))
    for k in range(1, turns + 1):
        L.append(f"G3 X{f3(cx + P_HELIX_R)} Y{f3(cy)} Z{f3(zt * k / turns)} I{f3(-P_HELIX_R)} J0.000 F{P_FZ}")
    L.append(f"G3 X{f3(cx + P_HELIX_R)} Y{f3(cy)} I{f3(-P_HELIX_R)} J0.000 F{P_FZ}")
    t += (turns + 1) * 2 * math.pi * P_HELIX_R / P_FZ
    L += [f"G1 X{f3(cx)} Y{f3(cy)} F{P_F}"]
    for z in levels:
        L.append(safe(f"POCKET LEVEL Z{z:.3f}"))
        L += [f"G1 X{f3(cx)} Y{f3(cy)} F{P_F}", f"G1 Z{f3(z)} F{P_FZ}"]   # inside the full-depth bore: air
        px, py = cx, cy
        for dd, c in rings:
            # start each ring at its point nearest the current position
            k = int(np.argmin(np.hypot(c[:-1, 0] - px, c[:-1, 1] - py)))
            cc = np.r_[c[k:-1], c[:k + 1]]
            L.append(f"G1 X{f3(cc[0][0])} Y{f3(cc[0][1])} F{P_F}")
            t += math.hypot(cc[0][0] - px, cc[0][1] - py) / P_F
            L += [f"G1 X{f3(q[0])} Y{f3(q[1])}" for q in cc[1:]]
            t += float(np.sum(np.linalg.norm(np.diff(cc, axis=0), axis=1))) / P_F
            px, py = cc[-1]
        L += [f"G1 X{f3(cx)} Y{f3(cy)} F{P_F}"]        # back to the bore centre (across the cleared floor)
        t += math.hypot(px - cx, py - cy) / P_F + 0.2 / P_FZ
    L += [f"G0 Z{ZSAFE:.3f}"]
    return L, t, dict(rings=len(rings), levels=len(levels), bore_r=bore_r)


def header(name, lines):
    return [safe(f"Spiral cam edge clamp v4 - {name}")] + [safe(l) for l in lines] + \
           ["G21 G90 G17 G94", f"G0 Z{ZSAFE:.3f}"]


def spin_on():
    return [f"M3 S{S}", "G4 P3"]


def finish():
    return [f"G0 Z{ZSAFE:.3f}", "M5", "G0 X0 Y0", "M30"]


def write(path, L):
    for l in L:
        assert l.count("(") == l.count(")") <= 1, l
    open(path, "w").write("\n".join(L) + "\n")


def preview(P, plug, kc, kp, blank, touch, drv):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Polygon as MP
    fig, ax = plt.subplots(figsize=(9, 7.5))
    ax.add_patch(Rectangle((blank[0], blank[1]), blank[2] - blank[0], blank[3] - blank[1], fc="#eef0f3", ec="k", lw=1.2))
    for k in (kc, kp):
        ax.add_patch(MP(np.array(k.exterior.coords), closed=True, fc="#f6d9b8", ec="#c07020", lw=0.8))
        for i in k.interiors:
            ax.add_patch(MP(np.array(i.coords), closed=True, fc="#eef0f3", ec="#c07020", lw=0.8))
    ax.add_patch(MP(np.array(P.exterior.coords), closed=True, fc="#c9ced6", ec="k", lw=1.2))
    ax.add_patch(MP(np.array(plug.exterior.coords), closed=True, fc="#c9ced6", ec="k", lw=1.0))
    ax.add_patch(MP(np.array(pocket_region().exterior.coords), closed=True, fc="#9aa3ad", ec="k", lw=0.8))
    ax.add_patch(Circle((0, 0), G.PIVOT_D / 2, fc="white", ec="k"))
    ax.add_patch(Circle(drv, G.DRIVE_D / 2, fc="white", ec="k"))
    ax.plot(0, 0, "r+", ms=14, mew=2); ax.text(0.8, 0.8, "X0 Y0", color="r", fontsize=9)
    ax.plot(*touch, "bx", ms=10, mew=2); ax.text(touch[0] - 1, touch[1] + 1.2, "Z touch-off", color="b", fontsize=8, ha="right")
    ax.text(plug.centroid.x, plug.bounds[3] + 3.2, "T2 test plug\n(file 2)", ha="center", fontsize=8)
    ax.text(blank[0] + 1, blank[1] + 1, f"blank >= {blank[2] - blank[0]:.1f} x {blank[3] - blank[1]:.1f}\n"
            f"lower-left at X{blank[0]:.1f} Y{blank[1]:.1f}", fontsize=8, va="bottom")
    ax.text(drv[0] + 5, drv[1], "nut pocket\n(file 1)", fontsize=8, va="center")
    ax.set_aspect("equal"); ax.set_xlim(blank[0] - 3, blank[2] + 3); ax.set_ylim(blank[1] - 3, blank[3] + 3)
    ax.set_title("Cam v4 — machine view: blank BOTTOM-UP on the bed, origin = pivot centre\n"
                 "orange = trochoidal kerfs (file 3 cam, file 2 plug)", fontsize=10)
    ax.grid(alpha=0.3)
    fig.savefig(f"{OUT}/setup-preview.png", dpi=130, bbox_inches="tight")


def main():
    os.makedirs(OUT, exist_ok=True)
    P = part_polygon()
    plug = test_plug(P)
    dcx, dcy = drive_c()
    kerf_cam = P.buffer(W, resolution=48)
    kerf_plug = plug.buffer(W, resolution=48)
    allk = unary_union([kerf_cam, kerf_plug])
    bx0, by0, bx1, by1 = allk.bounds
    MARG = 4.0
    touch = (round(bx1 + 2.0, 1), 0.0)           # stock top, nothing is cut here
    blank = (bx0 - MARG, by0 - MARG, bx1 + MARG, by1 + MARG)
    bw, bh = blank[2] - blank[0], blank[3] - blank[1]
    common = [f"ONE SETUP: blank glued BOTTOM-UP with tape + CA, at least {bw:.1f} x {bh:.1f} mm",
              f"ZERO X0 Y0 = PIVOT CENTRE - blank lower-left corner at X{blank[0]:.1f} Y{blank[1]:.1f}, Z0 = TOP of stock",
              f"pivot X0 Y0, drive hole X{dcx:.3f} Y{dcy:.3f}, test plug left of the cam",
              f"Z TOUCH-OFF POINT for every tool: X{touch[0]} Y{touch[1]} - uncut stock top",
              f"STOCK {STOCK} mm - CALIPER IT, through-cuts go to Z{ZT:.3f}"]

    # 0 TRACE
    T = header("FILE 0 - cam-0-TRACE-spindle-off.nc - SPINDLE OFF",
               common + ["traces the outer edge of the cam kerf and the test-plug kerf at Z+2, then the blank corner - "
                         "check the blank covers all of it", "nothing is cut"])
    T += ["M5"]
    for g in (kerf_cam, kerf_plug):
        oe = np.array(g.exterior.simplify(0.02).coords)
        T += [f"G0 Z5.000", f"G0 X{f3(oe[0][0])} Y{f3(oe[0][1])}", "G0 Z2.000", "G4 P1"]
        T += [f"G1 X{f3(q[0])} Y{f3(q[1])} Z2.000 F600" for q in oe[1:]]
    T += ["G0 Z5.000", f"G0 X{f3(blank[0])} Y{f3(blank[1])}", "G0 Z2.000", "G4 P2",
          f"G0 X{f3(touch[0])} Y{f3(touch[1])}", "G4 P2", "G0 Z5.000", "G0 X0 Y0", "M30"]
    write(f"{OUT}/cam-0-TRACE-spindle-off.nc", T)

    # 1 T1 nut pocket
    PL, pt, pinfo = nut_pocket()
    F1 = header("FILE 1 - cam-1-T1-nut-pocket.nc",
                common + ["TOOL T1 1.5 mm single-edge O-flute - reach 8.51, pocket 4.2",
                          f"est {pt:.0f} min at F{P_F} - lubricant per your material",
                          f"settings from tools.yaml: DOC {P_DOC}, stepover {P_STEP}, F{P_F}"])
    F1 += spin_on() + PL + finish()
    write(f"{OUT}/cam-1-T1-nut-pocket.nc", F1)

    # levels for T2
    doc = DOC_T2 if DOC_T2 > 0 else T2_D
    n = int(math.ceil(-ZT / doc - 1e-9))
    levels = [round(ZT * k / n, 3) for k in range(1, n + 1)]

    # 2 T2 test plug
    TEST_LEVELS = int(os.environ.get("TEST_LEVELS", "2"))
    TL, tt, _, _, tinfo = troch(plug, levels[:TEST_LEVELS], "TEST PLUG")
    F2 = header("FILE 2 - cam-2-T2-TEST-plug.nc - T2 FIRST USE IN ALUMINIUM",
                common + [f"TOOL T2 1/8 in DLC single flute - flute 0.59 in - assumed cut dia {T2_D}",
                          "TOOL CHANGE from T1: re-zero Z ONLY at the touch-off point, X Y unchanged",
                          f"trochoidal kerf {W:.3f} round a 6 x 6 plug, first {TEST_LEVELS} of the cutout's levels "
                          f"[{-levels[0]:.3f} each, to Z{levels[TEST_LEVELS - 1]:.3f}] - same settings as the cutout",
                          f"F{F_CUT} cut arc, F{F_AIR} air arc, helix F{F_HELIX} {HELIX_PITCH}/rev - DIAL ~10k - WD-40",
                          f"est {tt:.0f} min",
                          f"MEASURE: kerf width, expect {W:.3f}; plug, expect 6.000 square",
                          f"cut dia = kerf - {2 * LOOP_R:.1f}, or {T2_D} - [plug - 6] ; plug wider at the bottom = the bit deflects",
                          "if the bit breaks or the kerf is off: STOP, regenerate with T2_D / DOC_T2, do not run file 3"])
    F2 += spin_on() + TL + finish()
    write(f"{OUT}/cam-2-T2-TEST-plug.nc", F2)

    # 3 T2 holes + cutout
    H1, h1t = helix_bore(0.0, 0.0, G.PIVOT_D, 0.0, ZT, "PIVOT HOLE")
    H2, h2t = helix_bore(dcx, dcy, G.DRIVE_D, -G.NUT_DEPTH + 0.2, ZT, "DRIVE HOLE - starts in the nut pocket")
    CL, ct, CB, cbt, cinfo = troch(P, levels, "CAM CUTOUT")
    t3 = h1t + h2t + ct
    F3 = header("FILE 3 - cam-3-T2-holes-cutout.nc - LAST",
                common + [f"TOOL T2 1/8 in, same zero as file 2 - cut dia {T2_D}",
                          f"OP1 pivot {G.PIVOT_D} bore, OP2 drive {G.DRIVE_D} bore - helix {HOLE_PITCH}/rev F{HOLE_F}",
                          f"OP3 trochoidal cutout, kerf {W:.3f}, {len(levels)} levels to Z{ZT:.3f}, spring pass + "
                          f"{CLEAN} cleanup - NO TABS, glued",
                          f"est {t3:.0f} min - DIAL ~10k - WD-40 - blow chips out of the bores"])
    F3 += spin_on() + H1 + H2 + CL + finish()
    write(f"{OUT}/cam-3-T2-holes-cutout.nc", F3)

    F3b = header("FILE 3b - cam-3b-T2-cleanup.nc - optional",
                 [f"TOOL T2, same zero as file 3, part still glued - {CLEAN} mm off the cam wall, est {cbt:.1f} min"])
    F3b += spin_on() + CB + finish()
    write(f"{OUT}/cam-3b-T2-cleanup.nc", F3b)

    info = dict(stock=STOCK, z_through=ZT, blank=[round(v, 2) for v in blank], blank_size=(round(bw, 1), round(bh, 1)),
                touch=touch, drive=(round(dcx, 3), round(dcy, 3)), levels17=levels, kerf=round(W, 3),
                pocket=pinfo, est_min=dict(f1=round(pt), f2=round(tt), f3=round(t3)), cutout=cinfo, plug=tinfo)
    try:
        preview(P, plug, kerf_cam, kerf_plug, blank, touch, (dcx, dcy))
    except ImportError:
        pass
    import json
    json.dump(info, open(f"{OUT}/gen-info.json", "w"), indent=1, default=float)
    print(json.dumps(info, indent=1, default=float))


if __name__ == "__main__":
    main()
