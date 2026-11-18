"""Spiral cam edge clamp — geometry, shared by make_cam.py (CadQuery model) and gen_cam.py (G-code).
Pure Python: no CadQuery here, so the G-code side runs on the system python.

v4 NO counterbores — both bolt heads sit on top. Every machined feature
is then on the cam's BOTTOM face or goes straight through, so the whole part is cut in ONE
setup with the blank glued bottom-up: nut pocket, two holes, cutout. Done.

Top-view coordinates (looking down on the cam as used): origin = pivot centre, spiral grows
counter-clockwise from +X. The G-code mirrors X because the cam is cut upside down.
"""
import math

H = 12.7              # plate thickness = cam height (measure the stock; gen_cam takes STOCK)
R0 = 13.0             # smallest working radius (pivot axis to the part's edge)
R_MAX = 20.0          # largest working radius
SPIRAL_DEG = 270.0    # spiral span; the rest of the turn is a plain arc at R0
R_STEP = 3.3          # concave corner at the step (>= the 1/8 in cutter's radius + kerf loop)
R_TIP = 1.0           # round the sharp tip at R_MAX
PIVOT_D = 6.6         # M6 clearance — pivot bolt into the T-nut / grid hole
DRIVE_R = 12.25       # drive bolt centre from the pivot
DRIVE_DEG = 240.0     # in the big end of the spiral
DRIVE_D = 5.5         # M5 clearance
NUT_AF = 8.1          # M5 nut 8 AF -> slip fit, flats stop it turning
NUT_DEPTH = 4.2       # nut 4.0 thick sits inside, clear of the bed (pocket in the BOTTOM face)
RELIEF_D = 1.6        # hex corner reliefs, cut by the 1.5 mm tool
RELIEF_INSET = 0.4    # relief centre this far inside the sharp hex vertex
MU = 0.15             # assumed friction, for the self-lock check
N_PTS = 240

TH = math.radians(SPIRAL_DEG)
K = (R_MAX - R0) / TH                       # mm per radian


def r_at(theta):
    return R0 + K * theta


def outline():
    """Cam outline, top view, CCW polygon points (sharp step; fillets added by the consumer)."""
    pts = []
    for i in range(N_PTS + 1):
        t = TH * i / N_PTS
        r = r_at(t)
        pts.append((r * math.cos(t), r * math.sin(t)))
    pts.append((R0 * math.cos(TH), R0 * math.sin(TH)))
    n_arc = 30
    for i in range(1, n_arc):
        t = TH + (2 * math.pi - TH) * i / n_arc
        pts.append((R0 * math.cos(t), R0 * math.sin(t)))
    return pts


def drive_xy():
    a = math.radians(DRIVE_DEG)
    return DRIVE_R * math.cos(a), DRIVE_R * math.sin(a)


def hex_pts(cx, cy):
    r_v = NUT_AF / math.sqrt(3)
    return [(cx + r_v * math.cos(math.radians(60 * i)), cy + r_v * math.sin(math.radians(60 * i))) for i in range(6)]


def relief_centres(cx, cy):
    c = NUT_AF / math.sqrt(3) - RELIEF_INSET
    return [(cx + c * math.cos(math.radians(60 * i)), cy + c * math.sin(math.radians(60 * i))) for i in range(6)]


def numbers():
    r_v = NUT_AF / math.sqrt(3)
    lock_deg = math.degrees(math.atan(MU))
    return dict(
        throw=R_MAX - R0, reach_min=R0, reach_max=R_MAX,
        mm_per_quarter_turn=K * math.pi / 2,
        slope_deg_at_R0=math.degrees(math.atan(K / R0)),
        slope_deg_at_RMAX=math.degrees(math.atan(K / R_MAX)),
        self_lock_limit_deg=lock_deg,
        drive_hole_to_pivot_hole=DRIVE_R - DRIVE_D / 2 - PIVOT_D / 2,
        nut_pocket_to_pivot_hole=DRIVE_R - (r_v - RELIEF_INSET + RELIEF_D / 2) - PIVOT_D / 2,
        nut_pocket_to_edge=r_at(math.radians(DRIVE_DEG)) - DRIVE_R - (r_v - RELIEF_INSET + RELIEF_D / 2),
        drive_screw_len_max=H - 0.5,          # under-head length so the tip stays 0.5 above the bed
        nut_engagement_with_m5x12=NUT_DEPTH - (H - 12.0),   # head on top, tip at H-12 above the bed
    )
