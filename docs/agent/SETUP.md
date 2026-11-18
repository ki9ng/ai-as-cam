# First-run setup (agent-driven)

Installing ai-as-cam means: the user opens this repo in an AI coding agent (Claude Code, Codex, etc.), and the agent builds their config by interviewing them.

When `machines/` holds only `example.yaml`, or the user asks to set up:

1. Ask one question at a time. Don't guess values; if the user doesn't know one, leave it out and say which check it disables.
2. Machine: name, controller/firmware (GRBL, FluidNC, LinuxCNC, Marlin...), travel X/Y/Z, max feed per axis or controller clamp, spindle type and RPM range, rotary axis if any.
3. Workholding and probing: probe available? zero conventions (stock top = Z0? corner or center?).
4. Tools: for each tool — type, diameter, flutes, flute length, and any limits the user has measured (DOC, feed, chipload).
5. Materials the user cuts.
6. Write `machines/<name>.yaml` and `tools/<name>.yaml`, show them to the user, and commit only after they confirm.
7. Run the test suite to confirm the install works.

Never invent speeds, feeds or limits. Measured user values beat any default.
