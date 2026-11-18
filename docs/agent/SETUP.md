# First-run setup (agent-driven)

Installing ai-as-cam means: the user opens this repo in an AI coding agent (Claude Code, Codex, etc.), and the agent builds their config by interviewing them.

When `machines/` holds only `example.yaml`, or the user asks to set up:

1. Ask one question at a time. Don't guess values; if the user doesn't know one, leave it out and say which check it disables.
2. Machine: name, controller/firmware (GRBL, FluidNC, LinuxCNC, Marlin...), travel X/Y/Z, max feed per axis or controller clamp, spindle type and RPM range, rotary axis if any.
3. Workholding and probing: probe available? zero conventions (stock top = Z0? corner or center?).
4. Tool library (`tools/<name>.yaml`, format in `tools/example.yaml`): for each tool, type and geometry (diameter, flutes, flute length, stickout, corner radius or V angle and tip), tool material/coating, and per workpiece material: RPM, feed, plunge, DOC, stepover. Mark each number `measured` or `starting`, and each tool/material pair `untested`, `coupon_passed` or `proven`. Unknown values stay out.
5. Materials the user cuts.
6. Write `machines/<name>.yaml` and `tools/<name>.yaml`, show them to the user, and commit only after they confirm.
7. Run the test suite to confirm the install works.

Never invent speeds, feeds or limits. A `starting` number is one the user chose to try (e.g. from the tool maker), not one you made up. Measured user values beat any default.
