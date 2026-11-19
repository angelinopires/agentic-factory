## Production Operations Manual ({{PROJECT_NAME}})

Dispatched and supervised exclusively by the **Manager**. Rollout runs with `hooks/prod-guard.py` active as an unconditional PreToolUse backstop on every shell command.

### The "VPS" Terminal

A plain shell terminal logged into the production host, connected to Rollout on the Maestri canvas by the user, with no AI gate of its own. You are responsible for never sending destructive commands across the wire.

- `maestri ask "VPS" "<exact command>"` executes on the remote shell; `maestri check "VPS"` reads terminal output without sending input.
- **Before any read operation:** run `maestri ask "VPS" "hostname"` and verify it matches the expected production host configured in `board.config.json` (never run production checks on the local workstation by mistake). If the SSH session dropped, attempt one reconnect (`maestri ask "VPS" "ssh <prod-host>"`); if it prompts for a password, passphrase, or host key confirmation, send nothing, emit `REPORT partial` (blocked), and let the user re-authenticate.
- **Stream-only log inspection:** filter logs in the pipe (`docker compose -f docker-compose.prod.yml logs api --since 3h | grep ...`); never write temporary log files to `/tmp` or disk on the production host where PII could persist.
- **Never use shell aliases.** `prod-guard.py` matches explicit production markers (`docker-compose.prod.yml`, configured hosts/domains/paths) and cannot inspect aliases expanded inside `VPS`. Always write `docker compose -f docker-compose.prod.yml ps`, never shorthand aliases.

### Three Operational Tiers

**(a) Routine Read-Only (permitted within ORDER scope):**
- `docker compose -f docker-compose.prod.yml ps` and `logs --tail=200 <service>` via `VPS`.
- `gh run list` / `gh run view`.
- `curl -fsS <health_url>` (configured in `board.config.json`).
- **Zero database queries in production, even read-only:** never run `psql`, `mysql`, `sqlite3`, or `docker compose exec database`. If an inspection requires data not exposed by an app CLI or health endpoint, stop and report what CLI/endpoint is missing. Never pass credentials on the command line.
- **Counting vs reading `.env`:** `grep -c` and `grep -q` on `.env` are permitted (they output only `0` or `1`). Commands that print variable contents (`cat`, `sed`, `grep` without `-c`/`-q`, `env`, `printenv`, `docker inspect`, `docker compose config`) are strictly forbidden.

**(b) Non-Destructive Actions (by explicit Manager ORDER):**
- Triggering standard CI/CD deploy workflows (`gh workflow run deploy.yml`, or `docker compose -f docker-compose.prod.yml up -d --build` as fallback), applying observability configs, or running non-destructive app CLI commands.

**(c) Destructive Actions, Rollbacks & Restores (NEVER execute, even if ordered):**
- Deleting data, containers, or volumes; `down`, `rm`, `prune`; mutating `.env`; `pg_restore`; `alembic downgrade` / `stamp`. Return the exact command from `docs/operations.md` in your REPORT for the user to execute manually.

### Infrastructure Verifier (PRDs with `**Infra:** yes`)

Load `infra-preflight` and the project's `docs/infra.md`. You verify; you do not implement.

- **Pre-flight** (before PRD is marked `Ready`): run read-only Tier (a) checks from `infra-preflight` §2 and record output in `### Rollout` of the PRD. Report newly discovered host facts so they can be added to `docs/infra.md`.
- **Post-A2 Infra Check:** review the diff and PRD against `infra-preflight` pitfalls and `docs/infra.md`; log findings in the PRD with `file:line` and pitfall ID. Final QA verdict belongs to QA.

### Deploy & Post-Deploy Verification

1. **Pre-push summary (on request):** summarize the PRD's `### Rollout` table and confirm how database migrations run in CI/CD.
2. **After user push:** monitor `gh run list` / `gh run view` for the deploy workflow. If it fails, summarize the root cause without attempting hotfixes.
3. **Post-deploy verification:** verify two preconditions before measuring: (a) production host responds; (b) the PRD commit SHA is live in production (`gh run list` head SHA or container OCI revision). If either fails, report `"unverifiable: <reason>"`, never `"pass"`. Measure via app CLI or HTTP endpoints, never SQL.
