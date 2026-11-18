"""Finished-part checks on a replayed Stock. Masks are boolean arrays on stock.grid().

Build masks however you like (shapely contains_xy, numpy math, rasterized STL...).
"""
import numpy as np


def _where(stock, sel):
    iy, ix = np.argwhere(sel)[0]
    return f"X{stock.xs[ix]:.2f} Y{stock.ys[iy]:.2f}"


def untouched(stock, mask, name="part", tol=1e-6):
    bad = mask & (stock.h < -tol)
    return [f"GOUGE in {name} at {_where(stock, bad)}"] if bad.any() else []


def at_depth(stock, mask, z, name="floor", tol=0.02):
    d = stock.h[mask]
    if d.size and not (np.abs(d - z) < tol).all():
        return [f"{name} not at Z{z:g}: {d.min():.3f}..{d.max():.3f}"]
    return []


def through(stock, mask, z_through, name="cut", tol=0.02):
    bad = mask & (stock.h > z_through + tol)
    return [f"{name} not through at {_where(stock, bad)}"] if bad.any() else []
