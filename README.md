# ai-as-cam

**No CAM software. An AI writes the toolpath generator for each part, and automated gates decide whether the G-code may run.**

This repo holds the reusable parts of that workflow:

- **Verifier / gates**: re-read the G-code from disk and replay it against the stock and part (gouges, leftover material, travel limits, feeds).
- **Air-time audit**: measure how much of a program cuts nothing.
- **G-code parser**: reads the file from disk for the gates.
- **Agent instructions**: rules an AI agent follows when doing CAM work (`docs/agent/CLAUDE.md`).
- **Worked example**: a cam edge clamp, from part to passing gates (`examples/cam-edge-clamp/`).

## The loop

1. State the part, stock, machine and tools.
2. The AI writes or edits a per-part generator. The generator is the CAM; never hand-edit the `.nc`.
3. Run the gates on the file as written to disk.
4. Only a passing, versioned file goes to the machine, and only when the operator says go.

See `docs/method.md`. Each gate exists because something went wrong. When something goes wrong for you, you and your agent write a post-mortem and turn the fix into config, a rule or a check; see `docs/postmortems.md`.

Everything lives in your own clone as plain files in git: config, rules, post-mortems and G-code versions. No server needed.

## Status

Pre-release. The verifier, air-time audit and the cam edge clamp example work and pass their tests. Planned later (optional): probe height map + skew correction for warped or out-of-square stock.

## Install

Open this repo in an AI coding agent (Claude Code, Codex, ...) and ask it to set up ai-as-cam. It clones the repo, interviews you about your machine and tools, and writes your config. See `docs/agent/SETUP.md`.

## Configuration

Machine and tool specifics live in `machines/*.yaml` and `tools/*.yaml`. The examples are templates for a 3018-class GRBL/FluidNC router; copy and edit them for your own machine.

## License

GPL-3.0. See `LICENSE`.
