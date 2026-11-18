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


def _val(v):
    return v["value"] if isinstance(v, dict) and "value" in v else v


def tool_data(tools_yaml, tool_id, material, op=None):
    """Flatten one tool's settings for a material (and optional op) to plain numbers.

    Returns {"geometry": {...}, "status": str, **params}. Raises KeyError if the tool or
    material isn't in the library, so a generator can't silently fall back to a guess.
    """
    tools = {t["id"]: t for t in tools_yaml["tools"]}
    t = tools[tool_id]
    m = t["materials"][material]
    src = m.get("ops", {}).get(op, {}) if op else {}
    base = {k: v for k, v in m.items() if k not in ("ops", "status")}
    params = {k: _val(v) for k, v in {**base, **src}.items()}
    return {"geometry": t["geometry"], "status": m.get("status", "untested"), **params}
