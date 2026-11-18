# Method

1. **Define**: part geometry, stock size, workholding, machine profile, tool list.
2. **Plan in prose**: op order, tool per op, strategy. Agree it with the operator before writing code.
3. **Generate**: a per-part Python generator emits G-code. Every output gets a version in its header and a new filename or tag; never overwrite a previous version.
4. **Verify**: gates re-read the file from disk (not the generator's in-memory copy) and must all pass.
5. **Audit**: air-time audit on every file; fix paths that cut mostly air.
6. **Run**: operator uploads and starts the cut. The agent never starts a cut.
