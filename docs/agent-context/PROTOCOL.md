# Token protocol

Goal: one small index + one living state file, not a growing conversation dump.

## Every coding session

1. Read `INDEX.md` and `STATE.md` once. Do not re-read them later in the same chat unless you edited them.
2. Open **only** the INDEX row that matches the task.
3. Find code with **Grep** (symbol, route, permission). Read files with **offset/limit**.
4. Implement the smallest change that matches `docs/` invariants.
5. Before finishing: rewrite `STATE.md` so the next agent does not need this chat.

## Budget

| Action | Limit |
|--------|--------|
| Always-on Cursor rule | Tiny pointer only (already in `.cursor/rules`) |
| `STATE.md` | ≤80 lines |
| `INDEX.md` | Add a **row**, not a paragraph, when a new spec appears |
| New context file | Only if a spec is too large and a 40-line extract is reused often |
| Chat replies | Lead with the change; no recap of all phases |

## After a phase / PR

Replace in `STATE.md`:

- Checkout / API version
- Next recommended task + the 4–6 files to read
- Last change (one bullet)
- Commands if they changed

If you added `docs/foo.md`, add **one row** to `INDEX.md`.

Do not copy PR descriptions, test logs, or stacked-branch novels into STATE.

## Git

- Feature branches: `cursor/<descriptive-name>-dfc8`
- Stack PRs on the current base listed in STATE
- Commit STATE with the feature (same commit or same PR)

## What not to load

- Entire `docs/schema.md` unless editing schema
- Entire `docs/milestones.md` unless changing phase order
- All four apps when the change is backend-only (and vice versa)
