# Project Instructions

## Required documentation

Before planning or modifying code, read:

- `docs/BLOCKABLE_BLOCK_DESIGNER_PLAN.md`
- `docs/BLOCKABLE_COMBAT_SYSTEM.md`

Follow that document unless the current user request explicitly overrides it.

`docs/BLOCKABLE_COMBAT_SYSTEM.md` is an upstream combat contract owned by the
Blockable game project. Do not change its combat rules from this Designer task.
Update the Designer implementation and its other documents to follow it, especially
section 7.4.

When importing older data, convert effects only when their meaning can be mapped to a
7.4 `type`, `target`, integer `value`, and complete
`parameters.id/duration/intensify` without guessing. Treat `reference_id` as read-only
legacy input and migrate it to `parameters.id`; never write it in new JSON. Surface
ambiguous legacy data for review rather than inventing runtime semantics.

## Documentation maintenance

Do not update project documents automatically when code, behavior, or data changes.
Update documents only when the user explicitly requests a documentation update. When
the user does request it, synchronize the relevant plan, manual, update history, and
`docs/BLOCKABLE_BLOCK_DESIGN_CODEX_INTERACTION_INSTRUCTION.md` with the current code
and authoritative JSON as applicable.

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
