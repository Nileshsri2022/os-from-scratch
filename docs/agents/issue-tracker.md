# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files — no external tracker.
(Adapted from the `setup-matt-pocock-skills` local template; where this file
differs from the template, this file wins — it records our actual convention.)

## Conventions

- One feature per directory: `.scratch/<feature-slug>/` (today: `os-from-scratch`)
- **The spec lives at `docs/spec.md`** — a deliberate deviation from the template's
  `.scratch/<feature-slug>/spec.md`, recorded here so skills look in the right place
- Implementation issues are one file per ticket at
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in
  dependency order, never a single combined tickets file
- Each ticket carries a `Blocked by:` line (its blocking edges) and a `Status:`
  line near the top. Our status vocabulary: `todo` → `doing` → `done (YYYY-MM-DD)`
  (no triage role strings — the `triage` skill is not installed; revisit here if
  it ever is)
- Per-ticket shape is the owner's docs-first template (see `AGENTS.md`):
  Goal → Concepts → Design → Steps (checkboxes) → Verify → Result & shortcuts.
  `Result` is the close-out record: what actually happened, demo/test evidence,
  labelled shortcuts
- `docs/STATUS.md` is the human-readable step-by-step tracker over all of the
  above; it summarises, it never overrides ticket files

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if
needed) — except specs, which are published to `docs/spec.md`.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or
the issue number directly.
