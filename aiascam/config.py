"""Load user machine/tool config. Missing values disable the checks that need them."""
import yaml


def load(path):
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def feed_limits(machine):
    """Map a machine profile to run_file limits. Omits anything not configured."""
    lim = {}
    mf = machine.get("max_feed_mm_min") or {}
    xy = [mf[k] for k in ("x", "y") if k in mf]
    if xy:
        lim["feed_xy"] = min(xy)
    if "z" in mf:
        lim["feed_z"] = mf["z"]
    return lim
