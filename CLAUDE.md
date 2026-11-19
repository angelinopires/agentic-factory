# Agentic Factory (`projects/agentic-factory/`)

Public, provider-agnostic agentic engineering framework powered by **Maestri** (multi-agent terminal orchestration), deterministic on-disk state (`planning/`), cryptographic execution/QA gates (`scripts/`, `hooks/`), and 22 portable skills. Built from the production harness behind **SeuTrampo AI**.

---

## Core Architecture

1. **100% English Repository:** All filenames, scripts, CLI flags, `ORDER`/`REPORT` protocol messages, role prompts, skills, rules, and documentation live in English. The user's conversational language (`pt-BR`, `en`, etc.) is a runtime parameter in `board.config.json`.
2. **Zero Local Leakage:** No file in this repository may contain hardcoded machine paths (`/Users/angelino`), private IPs, or personal emails. All paths resolve dynamically from `board.config.json` or environment variables (`MAESTRI_WORKSPACE_ROOT`, `MAESTRI_PLANNING_DIR`, `MAESTRI_PROJECT_DIR`).
3. **One Fact = One File:** State lives on disk (`progress.md`, `history.md`, `epics/`, `ready/`, `archive/`, `runs/`), surviving any context reset or 200k ceiling.
4. **Adaptive Multi-Harness Routing:**
   - **2+ AI CLIs (`claude`, `codex`, `agy`):** Enables blind dual research, cross-family code review (A1), and zero-downtime quota fallbacks.
   - **1 AI CLI:** Maps active roles across that provider's tiers (`high` for Manager, `medium` for workers, `browser` for QA) and runs blind research across two isolated sessions.
5. **Modular Board Roster:**
   - **Core roles (always active):** `Manager`, `Explorer`, `Dev`, `QA`.
   - **Conditional roles (enabled by `/init-board` via `board.config.json`):** `Dev Front` + `Dev Back` split, `Designer`, `Writer`, `Rollout` + `VPS`, `Blind Reviewer`.

---

## Target Repository Layout

```text
projects/agentic-factory/
├── CLAUDE.md                        # Context & verification commands (AGENTS.md -> CLAUDE.md)
├── README.md                        # TechLino-voice README with Mermaid/SVG diagrams & Maestri guide
├── board.config.example.json        # Canonical configuration schema (paths, stack, roles, models, prod markers)
├── sync-manifest.json               # Source-to-target mapping consumed by /sync-agentic-factory
├── board/                           # Modular Maestri role prompts (English, parameterized)
│   ├── README.md                    # Role assembly & recruit reference
│   ├── core.md                      # Shared board kernel (~300 words max)
│   ├── manager.md                   # Single leader role
│   ├── explorer.md                  # Discovery, /prd & /prd-ship role
│   ├── designer.md                  # Product design & static HTML options role
│   ├── writer.md                    # UX copy & humanizer role
│   ├── dev.md                       # Engineering execution & TDD role
│   ├── qa.md                        # A1/A2/B verification role
│   ├── rollout.md                   # Production & infra preflight role
│   ├── playbook.md                  # Operational procedures, quota fallbacks, resets
│   ├── qa-manual.md                 # Stage A1, A2, B verification manual
│   ├── rollout-manual.md            # 3-tier production operations manual
│   ├── map.md                       # Board lookup table template
│   ├── plan.md                      # 1-page plan template
│   └── settings/                    # Harness settings templates (agy, qa, rollout)
├── scripts/                         # Deterministic governance & onboarding CLI tools (Python 3 stdlib)
│   ├── diagnose.py                  # Detects installed AI CLIs (maestri, claude, codex, agy) & repo topology
│   ├── compile-board.py             # Compiles board/*.md + board.config.json into Maestri roles & symlinks
│   ├── order.py                     # SHA-256 ORDER/REPORT state machine, authorization quote check & reconcile
│   ├── qa-proof.py                  # Cryptographic test proof tied to git commit, tree, dirty hash & lockfiles
│   ├── role-check.py                # 3-layer drift check (board/*.md -> role.json -> CLAUDE.md/AGENTS.md)
│   ├── prd-cost.py                  # Token & USD-equivalent cost attribution across Claude & Codex logs
│   ├── agy-trust.py                 # Pre-trusts Maestri role folders in Antigravity CLI
│   └── manager-context.sh           # Context usage monitor in k-tokens
├── hooks/                           # PreToolUse & PostToolUse guardrails
│   ├── pre-tool-use.js              # Blocks --no-verify, git push, --amend, compose down, rm -rf, sudo, >800 lines
│   ├── context-ceiling.py           # 170k warn / 200k deny with exemptions for maestri, order.py & runs/
│   └── prod-guard.py                # Blocks direct SQL/DDL/destructive commands against configured prod markers
├── templates/                       # Planning & taste/voice starter templates
│   ├── planning/                    # PLANNING_GUIDE.md, _template_prd.md, _template_epic.md, progress.md, history.md
│   ├── design/                      # anti-slop.md, taste-rules.md
│   ├── voice/                       # brand-voice.md, project-sheet.md
│   └── githooks/                    # pre-commit, pre-push
├── skills/                          # 22 portable English skills + /init-board
│   └── <skill-name>/SKILL.md
├── rules/                           # Base engineering rules (git-workflow, coding-style, testing, security, communication)
├── docs/
│   ├── architecture.html            # Standalone interactive visual workflow & topology explorer
│   └── case-study-seutrampo/        # Sanitized real-world evidence: cases.md, sample PRD, sample retro, metrics
└── tests/                           # Unit & integration tests (unittest/pytest, ≥70% coverage)
    ├── test_order.py
    ├── test_qa_proof.py
    ├── test_context_ceiling.py
    ├── test_prd_cost.py
    ├── test_prod_guard.py
    ├── test_diagnose_and_compile.py
    └── test_leak_and_portability.py
```

---

## Comandos de Verificação

Run from `/Users/angelino/Workspace/projects/agentic-factory`:

```bash
# 1. Full unit test suite (scripts, hooks, config compiler, portability checks)
python3 -m unittest discover -s tests -p "test_*.py" -v

# 2. Zero local-path / PII / PT-BR filename leak check
python3 -m unittest tests/test_leak_and_portability.py -v

# 3. Role prompt word/line budget check (core.md <= 500 words, role files <= 400 words)
python3 scripts/compile-board.py --check-budgets
```
