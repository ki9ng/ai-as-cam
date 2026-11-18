# Post-mortems: how your setup gets better

Your copy of ai-as-cam learns from your own mistakes. The rules that matter for your
machine, tools and materials are ones you find by cutting. This repo doesn't ship them.

## When to write one

Any time a result doesn't match what you expected: a broken bit, a gouge, a check that
passed when it shouldn't have, a program that spent half its time cutting air, a
regenerate that wiped out a file you needed. Not just crashes.

## How

The user and the agent write it together, right after the failure, while the details are fresh:

1. **What happened.** Facts only: file, line, tool, material, what you saw.
2. **Why.** The real cause, not the first guess. Say whether it was measured or assumed.
3. **The fix.** Make it concrete, and put it where it will be applied automatically next time:
   - a **number** in your `machines/` config or tool library (a feed, depth or limit you measured; add the post-mortem to that tool's `history`),
   - a **rule** in your agent file (how the agent should plan or write generators), or
   - a **check** (a new gate, or a test that would have caught it).
4. **Proof.** Re-run the gates or tests and show that the fix catches the original problem.

Save each one as a dated file in `postmortems/` in your own clone and commit it. One page
each, short. The agent reads them before planning a new job.

## What the agent must do

- Offer a post-mortem whenever a result misses expectation. Don't just correct the output.
- Never fix a failure only in the one generator that hit it. If the cause can happen again,
  it goes into config, rules or a check.
- Keep machine-specific lessons in your config and rules, not in the shared code.

## Example (from the author's machine)

> **What:** a relief-carving program spent ~90% of one pass cutting air.
> **Why:** the path logic cut a whole lane if any point touched material; the check only
> looked at the part, not the path.
> **Fix:** a new check, the air-time audit, now runs on every file.
> **Proof:** the audit flags the old file and passes the fixed one.

That one became a shared gate because it applies to any machine. Most of yours won't.
