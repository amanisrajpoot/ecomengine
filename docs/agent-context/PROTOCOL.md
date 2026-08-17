# Token protocol

## Discovery (mandatory)

1. `INDEX.md` → `STATE.md` once per conversation.
2. Choose **one**: `PHASES.md` (numbered phase) **or** `ROUTES.md` (change type) **or** `MAP.md` (known module).
3. Open **only** the paths those rows name. Use Read `offset`/`limit` on specs ([SCHEMA.md](./SCHEMA.md)).
4. Grep **inside** that module path. Do **not** Glob `**/*` to find files.
5. If you create a file, **register it in MAP.md** the same PR (and PHASES/INDEX if a new domain doc appears).

## Budget

| Item | Limit |
|------|--------|
| `STATE.md` | ≤80 lines, replace not append |
| Spec reads | One heading / one SCHEMA slice |
| Apps | Only the app in the ROUTES/PHASES row |
| Chat | No phase recap |

## After a PR

Update `STATE.md` (version, next phase). Tick MAP empty→files. Fix SCHEMA.md offsets if schema.md shifted.

## Git

Branches: `cursor/<name>-dfc8`. Base = STATE “Base branch”.
