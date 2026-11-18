# Agent rules for AI-as-CAM work

- The generator is the CAM. Edit the generator, never the `.nc` output.
- Version every output. Never overwrite or regenerate G-code without a recoverable prior version (git commit or tag).
- Verify the file as it exists on disk, after it is written.
- Run the air-time audit on every file.
- Load machine limits and tool data from `machines/` and `tools/`; never assume generic speeds and feeds.
- Never start a cut, jog, or send G-code to a machine without the operator's explicit go.
- When a result doesn't match expectation, write a post-mortem with the user (see `docs/postmortems.md`) and put the fix into config, rules or a check.
- Read `postmortems/` before planning a new job.
- Keep everything in this repo as files: config, rules, post-mortems, G-code versions. Don't assume a server or remote access.
- When planning a job, read `docs/agent/strategies.md`. Name each strategy you choose and why, in the plan, so the user can see and override it.
- Every feed, speed, DOC and stepover comes from the tool library. If the tool/material pair is `untested`, plan a test coupon first. After a cut, propose library updates (values to `measured`, status, history) and write them once the user confirms.
