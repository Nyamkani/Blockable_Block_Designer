# Project Instructions

## Required documentation

Before planning or modifying code, read:

- `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
- `docs/RULE_SCHEMA_1_1.md`
- `docs/BLOCKABLE_COMBAT_EFFECT_STANDARD.md`
- `docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md`


Follow that document unless the current user request explicitly overrides it.

`docs/BLOCKABLE_COMBAT_EFFECT_STANDARD.md` is a read-only upstream contract owned by
the Blockable game project. Never edit it in this Designer repository. Update the
Designer implementation and its other documents to follow the latest copied standard.

When importing or saving older data, merge custom effect definitions that are clearly
equivalent to a standard effect into the standard ID and parameters, then remove the
duplicate definition. Preserve effects with additional or ambiguous runtime semantics
as custom effects instead of guessing.

## Documentation maintenance

When the project plan, program behavior, JSON contract, package path, execution command,
or required workflow changes, update
`docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md` in the same task.

Documentation filenames added or renamed from now on must use uppercase names
(the `.md` extension remains lowercase).

## JSON-driven handoff workflow

When the user designates a newly written Blockable design JSON:

1. Treat that JSON as the authoritative data source.
2. Parse and validate it instead of copying counts or IDs from an older document.
3. Rewrite `docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md` so its
   current-data snapshot and application instructions match that JSON.
4. Use the JSON and the rewritten instruction document together when applying the
   design to another project.
5. In the target project, read and follow its own `AGENTS.md` before making changes.

The JSON is authoritative for game data. The instruction document explains how to
interpret and integrate that data; it must not override the JSON with stale values.
