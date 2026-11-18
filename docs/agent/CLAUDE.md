# Agent rules for AI-as-CAM work

- The generator is the CAM. Edit the generator, never the `.nc` output.
- Version every output. Never overwrite or regenerate G-code without a recoverable prior version (git commit or tag).
- Verify the file as it exists on disk, after it is written.
- Run the air-time audit on every file.
- Load machine limits and tool data from `machines/` and `tools/`; never assume generic speeds and feeds.
- Never start a cut, jog, or send G-code to a machine without the operator's explicit go.
- When a result doesn't match expectation, write a post-mortem: what went wrong, why, and the concrete fix.
