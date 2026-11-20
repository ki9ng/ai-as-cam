# First-run setup (agent-driven)

Installing ai-as-cam means: the user opens this repo in an AI coding agent (Claude Code, Codex, etc.), and the agent builds their config by interviewing them.

When `machines/` holds only `example.yaml`, or the user asks to set up:

0. **Gauge experience first.** Ask how long they've run this machine and what they already have written down: feeds-and-speeds notes, a spreadsheet, a tool library exported from other CAM (Vectric `.vtdb`, Carbide Create, Fusion), or G-code that has run well. Import whatever they hand over before asking anything else, then ask only about what's still missing.
   - **Experienced user with records:** take values from their records and confirm them in batches. Spend the questions on depth instead: rigidity, deflection limits, chip loads they trust, finish and tolerance expectations. Numbers they've actually run are `measured`; tool/material pairs they've cut repeatedly can be `proven` on their history.
   - **New user:** don't ask for what they can't know yet. Keep it to machine basics and the tools in hand, use the maker's numbers as `starting` values, and tell them to expect test coupons before real parts.
1. Ask one question at a time (batch confirmation of imported values is the exception). Don't guess values; if the user doesn't know one, leave it out and say which check it disables.
2. Machine: name, controller/firmware (GRBL, FluidNC, LinuxCNC, Marlin...), travel X/Y/Z, max feed per axis or controller clamp, spindle type and RPM range, rotary axis if any.
3. Workholding and probing: probe available? zero conventions (stock top = Z0? corner or center?).
4. Tool library (`tools/<name>.yaml`, format in `tools/example.yaml`): for each tool, type and geometry (diameter, flutes, flute length, stickout, corner radius or V angle and tip), tool material/coating, and per workpiece material: RPM, feed, plunge, DOC, stepover. Mark each number `measured` or `starting`, and each tool/material pair `untested`, `coupon_passed` or `proven`. Unknown values stay out.
   - **Research known tools.** If the user names a brand and model (or a link), search for the maker's published data: geometry and recommended speeds and feeds. Record them with `source: manufacturer` and the `url`. Maker charts usually assume rigid industrial machines; show the numbers to the user and let them choose a `starting` value for their machine. A manufacturer number never makes a tool `proven`; only cutting does.
5. Materials the user cuts.
6. Write `machines/<name>.yaml` and `tools/<name>.yaml`, show them to the user, and commit only after they confirm.
7. Run the test suite to confirm the install works.

Never invent speeds, feeds or limits. A `starting` number is one the user chose to try (e.g. from the tool maker), not one you made up. Measured user values beat any default.
