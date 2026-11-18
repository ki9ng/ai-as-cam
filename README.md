# ai-as-cam

**No CAM software. An AI writes the toolpath generator for each part, and automated gates decide whether the G-code may run.**

This repo holds the reusable parts of that workflow:

- **Verifier / gates**: re-read the G-code from disk and replay it against the stock and part (gouges, leftover material, travel limits, feeds).
- **Air-time audit**: measure how much of a program cuts nothing.
- **Probe height map + skew**: correct for stock that isn't flat or square.
- **G-code helpers**: safe comments, emitters.
- **Agent instructions**: rules an AI agent follows when doing CAM work (`docs/agent/CLAUDE.md`).
- **Worked example**: a cam edge clamp, from part to passing gates (`examples/cam-edge-clamp/`).

## The loop

1. State the part, stock, machine and tools.
2. The AI writes or edits a per-part generator. The generator is the CAM; never hand-edit the `.nc`.
3. Run the gates on the file as written to disk.
4. Only a passing, versioned file goes to the machine, and only when the operator says go.

See `docs/method.md`. Each gate exists because something went wrong; `docs/postmortems.md` gives one line per gate.

## Status

Early skeleton. Code is being extracted and generalized from working per-part tools.

## Configuration

Machine and tool specifics live in `machines/*.yaml` and `tools/*.yaml`. The examples are templates for a 3018-class GRBL/FluidNC router; copy and edit them for your own machine.

## License

GPL-3.0. See `LICENSE`.
