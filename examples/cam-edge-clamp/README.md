# Worked example: spiral cam edge clamp

A spiral cam that clamps a part against a fence. One setup, blank glued bottom-up:
nut pocket, two through holes, trochoidal cutout.

- `config/`      machine.yaml + tools.yaml: every feed, speed, depth and limit lives here
- `cam_geom.py`  geometry (pure Python)
- `make_cam.py`  optional CadQuery model
- `gen_cam.py`   the generator: this is the CAM. Edit it, never the `.nc`. No numbers hard-coded.
- `check_cam.py` gates via `aiascam.verify`; must print PASS before anything runs.

```
CONFIG=/path/to/your/config python3 gen_cam.py     # writes ./out/
CONFIG=/path/to/your/config python3 check_cam.py out
```

**The shipped `config/` is one specific 3018-class machine and tool set. Don't cut with it on yours.**
Point `CONFIG` at the config your agent built during setup.

Needs: numpy, shapely, pyyaml (matplotlib for the preview).
