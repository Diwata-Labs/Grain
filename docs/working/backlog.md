# Backlog

## Purpose

This document is the execution inventory for Grain.

It contains:
- concrete implementation tasks
- grouped by phase
- task status
- short execution-oriented descriptions

Status values: `draft` | `ready` | `in_progress` | `blocked` | `review` | `done`

Default status for new backlog items: `draft`

---

## Phase 1 — Repository Foundation and Core CLI ✓ CLOSED
9 tasks done — archived to `tasks/archive/phase-1/`

---

## Phase 2 — Documentation Registry and Validation ✓ CLOSED
9 tasks done — archived to `tasks/archive/phase-2/`

---

## Phase 3 — Task Packet System ✓ CLOSED
13 tasks done — archived to `tasks/archive/phase-3/`

---

## Phase 4 — Context Assembly and Model Routing ✓ CLOSED
13 tasks done — archived to `tasks/archive/phase-4/`

---

## Phase 5 — Review, Handoff, and Hardening ✓ CLOSED
9 tasks done — archived to `tasks/archive/phase-5/`

---

## Phase 6 — Adapter System Foundation ✓ CLOSED
7 tasks done — archived to `tasks/archive/phase-6/`

---

## Phase 7 — New-Project Onboarding Flow ✓ CLOSED
7 tasks done — archived to `tasks/archive/phase-7/`

---

## Phase 8 — Workflow Automation Runner Foundation ✓ CLOSED
11 tasks done — archived to `tasks/archive/phase-8/`

Key deliverables: `grain workflow next`, `grain workflow run`, `grain workflow explain`, `grain task prepare`, `grain prompt show`, verify bridge contract.

---

## Phase 9 — Orchestration Service Foundation ✓ CLOSED
7 tasks done — archived to `tasks/archive/phase-9/`

Key deliverables: `grain orchestrate scope/plan/accept`, `grain adapter list/show`, `OrchestratorPlan` domain model.

---

## Phase 10 — Structural Intelligence: Tree-sitter + Knowledge Graph ✓ CLOSED
6 tasks done — archived to `tasks/archive/phase-10/`

Key deliverables: tree-sitter structural extraction, NetworkX JSON knowledge graph, graph-assisted context selection. Absorbed FA-T01.

---

## Phase 11 — Distribution and Global Install ✓ CLOSED
5 tasks done (T05 deferred) — archived to `tasks/archive/phase-11/`

Key deliverables: PyPI publish flow, `uv tool install grain-kit`, Homebrew formula scaffold (deferred).

---

## Phase 12 — Automated Workflow Loop ✓ CLOSED
7 tasks done — archived to `tasks/archive/phase-12/`

Key deliverables: `grain workflow loop --steps N`, loop stop-condition hardening, machine-readable automation outputs.

---

## Phase 13 — Existing Project Adoption ✓ CLOSED
8 tasks done — archived to `tasks/archive/phase-13/`

Key deliverables: `grain onboard` for existing repos, bootstrap state detection, onboarding prompt hardening.

---

## Phase 14 — Document and Spreadsheet Adapters ✓ CLOSED
7 tasks done — archived to `tasks/archive/phase-14/`

Key deliverables: `docs_adapter`, `spreadsheet_adapter`, `.docx` and `.xlsx` extraction, `data_adapter` scaffold.

---

## Phase 15 — Workflow Hardening and Automation ✓ CLOSED
Tasks done — archived to `tasks/archive/phase-15/`

Key deliverables: phase-close enforcement, `grain workflow reconcile --fix`, runner resilience improvements.

---

## Phase 16 — Semantic Enrichment Layer ✓ CLOSED
Key deliverables: embedding-based document and code search, semantic similarity scoring for context selection, provider-agnostic embedding support (`local`, `openai`, `none`).

---

## Phase 17 — Ranking and Decision Layer ✓ CLOSED
Key deliverables: scored and ranked context source selection, weighted evidence-backed selection replacing static adapter priority rules.

---

## Phase 18 — Data Adapter ✓ CLOSED
Key deliverables: `data_adapter`, richer `.ipynb` context (cell outputs, dataset references), `.parquet`/`.h5`/`.hdf5` file patterns.

---

## Phase 19 — Community Adapter Registry ✓ CLOSED
Key deliverables: `grain adapter install <source>`, community adapter registry foundation, `contrib/community_adapter_registry/` structure, schema validation in CI.

---

## Phase 20 — Workflow Drift Remediation ✓ CLOSED
Key deliverables: field-reported bug fixes from production Grain usage (Assay + Obsidian), `grain workflow reconcile` improvements, bootstrap state robustness.

---

## Phase 21 — v0.3.0 Planning and Operator Surface Definition ✓ CLOSED
Key deliverables: v0.3.0 milestone contract, TUI scope locked, office artifact write-back scoped, verification bridge scoped.

---

## Phase 22 — TUI Foundation and Workflow Surfaces ✓ CLOSED
Key deliverables: `grain tui` — Textual-based terminal operator shell, workflow dashboard, backlog-by-phase view, packet artifact inspector, prompt preview.

---

## Phase 23 — Writable Office Artifacts ✓ CLOSED
Key deliverables: `.docx` and spreadsheet `propose`/`export`/`apply` write modes, review bundles, structural validators, packet-scoped write safety.

---

## Phase 24 — Desktop Integrations and Obsidian Support ✓ CLOSED
Key deliverables: `obsidian_adapter`, vault note context selection via wiki-link graph, MCP wrapper surface.

---

## Phase 25 — Database Adapter ✓ CLOSED
Key deliverables: `database_adapter`, schema/migration/query context selection, migration risk review guidance.

---

## Phase 26 — Crawler Adapter ✓ CLOSED
Key deliverables: `crawler_adapter`, crawl config/selector/extraction context selection, robots and rate-limit review guidance.

---

## Phase 27 — Recipe Layer and Operator Ergonomics ✓ CLOSED
Key deliverables: recipe execution primitives, operator ergonomics improvements, `grain workflow explain` hardening.

---

## Phase 28 — Assay Verification Integration ✓ CLOSED
Key deliverables: `grain verify submit/status/ingest`, verification-aware review/close gating, `verification_request.json` and `verification_result.json` packet artifacts.

---

## Phase 29 — Workflow Compliance Hardening ✓ CLOSED
Key deliverables: workflow compliance checks, `grain workflow guard` stub, `PROJECT_RULES.md` hardening.

---

## Phase 30 — v0.4.0 Planning and Toolkit Boundary Definition ✓ CLOSED
14 tasks done (TASK-0190 through TASK-0203). Doc snapshot at `docs/archive/phases/phase-30/`.

Key deliverables: v0.4.0 milestone contract locked, `grain suggest` spec, enforcement model spec, scaffold audit, docs audit spec, archive spec, CLI ergonomics spec, branch policy spec, upgrade enforcement spec.

---

## Phase 31 — DX Hardening and v0.4.0 Foundation ✓ CLOSED
8 tasks done (TASK-0204 through TASK-0211). Shipped as v0.3.1. Doc snapshot at `docs/archive/phases/phase-31/`.

Key deliverables: `grain workflow guard`, `grain hooks install/list/remove`, `grain docs audit`, `grain archive`, `grain status`, `grain doctor`, `grain upgrade --add-missing`, `upgrade_policy` and `branch_policy` manifest blocks, 13 new scaffold templates, `workflow.resume.md` prompt, stop reason constants.

---

## Phase 32 — v0.4.0 Proactive Assistance

> **Status:** ACTIVE — 10 tasks (P32-T01–P32-T10). v0.4.0 feature phase; scope reframed 2026-06-24 to a focused Proactive Assistance release (toolkit/recipe/apply moved to v0.5.0 — see `v0.5.0_contract.md`).

### P32 Notes
- v0.4.0 scope: grain suggest, phase close archiving, archive show, workflow next integration, grain notes full, workflow metrics, Pulse telemetry foundation, GitHub feedback (report + publish), docs hygiene
- T01 (spec) is satisfied by the canonical `docs/canonical/suggest_spec.md` → **done**
- T02 (implement) and T05 (workflow next integration) build on the locked spec
- T03, T06, T07, T08, T10 are independent and can run in parallel
- T09 depends on T06 (grain notes full implementation)
- T10 (docs hygiene) is founder-requested; fixes current_focus drift + adds an audit check
- Phase 31 is fully closed; no DX blockers remain

### P32-T01 — Write `grain suggest` spec
- **Status:** done (satisfied by canonical `docs/canonical/suggest_spec.md`)
- **Description:** Define the `grain suggest` command contract. Inputs: workspace state (open questions, doc gaps, backlog shape, recent closures). Outputs: ranked candidate tasks with draft context and plan seeds. Human approval gate: `grain suggest --accept <id>` promotes to a real packet; `grain suggest --prune` clears stale suggestions. Spec should cover output format, storage location, approval flow, and integration with `grain workflow next`.
- **Files:** `docs/working/suggest_spec.md` (new)
- **Model:** frontier_model
- **Dependencies:** none

### P32-T02 — Implement `grain suggest`
- **Status:** done
- **Description:** Implement `grain suggest` from the spec. Core logic: read workspace state, score candidate task types, generate ranked suggestions with draft context/plan seeds, write to `.grain/suggestions.json`. `grain suggest --accept <id>` creates a packet from the suggestion. `grain suggest --prune` clears stale entries. `--format json` output.
- **Files:** `src/grain/services/suggest_service.py` (new), `src/grain/cli/suggest.py` (new), tests
- **Model:** frontier_model
- **Dependencies:** P32-T01

### P32-T03 — Extend `grain phase close` to auto-archive task packets
- **Status:** done
- **Description:** When a phase is closed, automatically move all `tasks/P{N}-*` packet directories to `tasks/archive/phase-{N}/` alongside the existing doc snapshot. Behavior: (1) detect all packet dirs matching the phase prefix in `tasks/`; (2) create `tasks/archive/phase-{N}/` if absent; (3) move packets; (4) update `docs/archive/phases/phase-{N}/metadata.json` with `tasks_done` count and `tasks_archive` path. Add `--keep-tasks` flag to skip the move when a packet is being carried forward to the next phase.
- **Files:** `src/grain/services/phase_service.py`, `src/grain/services/archive_service.py`, `src/grain/cli/phase.py`, tests
- **Model:** frontier_model
- **Dependencies:** none

### P32-T04 — Extend `grain archive show` to surface packet list from task archive
- **Status:** done
- **Description:** `grain archive show --phase N` currently shows doc snapshot content. Extend it to also list the task packets in `tasks/archive/phase-{N}/` from the `tasks_archive` field in `metadata.json`. Output: phase metadata, doc snapshot files present, packet list with task ID and title (read from `task.md`). `--format json` output. If no task archive exists for a phase (pre-v0.4.0 close), surface the metadata note gracefully.
- **Files:** `src/grain/cli/archive.py`, `src/grain/services/archive_service.py`, tests
- **Model:** frontier_model
- **Dependencies:** none

### P32-T05 — Integrate `grain suggest` into `grain workflow next`
- **Status:** done
- **Description:** When `grain workflow next` evaluates the workspace and finds no obvious next task (e.g. `stop_reason: no_ready_tasks` or `backlog_empty`), automatically run the suggest engine and surface the top candidate in the workflow next output. Text output: inline suggestion block. JSON output: `suggestion` field with candidate. Does not write anything — suggestion is surface-only until `grain suggest --accept <id>` is called.
- **Files:** `src/grain/services/workflow_service.py`, `src/grain/services/suggest_service.py`, tests
- **Model:** frontier_model
- **Dependencies:** P32-T01, P32-T02

### P32-T06 — `grain notes` full implementation
- **Status:** done
- **Description:** Graduate `grain notes` from write-only stub to a queryable, actionable friction inbox. (1) Structured rows in `tooling_notes.md` with `id`, `type`, `status`, `created_at`, `body`; (2) `grain notes list` with `--type` and `--status` filters and `--format json`; (3) `grain notes show <id>` — full note detail; (4) `grain notes resolve <id>` — mark addressed with optional resolution note; (5) open notes with type `bug` or `friction` surface as `low`-severity findings in `grain docs audit`; (6) `grain notes add` improvements — auto-assign incremental ID, timestamp, default status `open`.
- **Files:** `src/grain/services/notes_service.py` (new), `src/grain/cli/notes.py` (extend), `src/grain/services/docs_audit_service.py` (extend), tests
- **Model:** frontier_model
- **Dependencies:** none

### P32-T07 — Workflow metrics — `grain metrics` command
- **Status:** done
- **Description:** Implement `grain metrics` for per-phase velocity and cost tracking. Reads task archive and docs archive to compute: (1) phase duration (open → close dates from metadata); (2) task count per phase; (3) stop-reason frequency from `.grain/last_workflow_state.json` history; (4) `grain metrics --phase N` for single-phase detail; (5) `grain metrics export` dumps full history as JSON. Writes `.grain/metrics_cache.json` with a 1-hour TTL. `--format json` output on all subcommands.
- **Files:** `src/grain/services/metrics_service.py` (new), `src/grain/cli/metrics.py` (new), tests
- **Model:** frontier_model
- **Dependencies:** none

### P32-T08 — Pulse telemetry foundation — opt-in event emission contract
- **Status:** done
- **Description:** Lay the Grain-side event emission contract for Pulse (the planned Diwata-wide telemetry layer). (1) Define a `TelemetryEvent` dataclass with `event_type`, `version`, `timestamp`, `payload` fields; (2) implement `telemetry_service.py` with a `emit(event)` method — fire-and-forget, never raises, logs to `.grain/telemetry_queue.jsonl` when endpoint is unreachable; (3) instrument key workflow moments: phase close, task close, `grain suggest --accept`, stop reason on `grain workflow next`; (4) opt-in via `telemetry.enabled: true` in `docs_manifest.yaml` or `GRAIN_TELEMETRY_ENDPOINT` env var; (5) no telemetry emitted unless explicitly enabled — default is off. Transport and aggregation are Pulse's responsibility; Grain only emits.
- **Files:** `src/grain/services/telemetry_service.py` (new), `src/grain/domain/telemetry.py` (new), instrumentation in phase/task/workflow/suggest services, tests
- **Model:** frontier_model
- **Dependencies:** none

### P32-T09 — `grain notes publish` — GitHub issue submission from CLI
- **Status:** done
- **Description:** Extend `grain notes` with a `publish` subcommand that submits a note directly to GitHub Issues. (1) `grain notes publish <id>` — formats the note as a GitHub issue (title from note body first line, body from full note + metadata); (2) applies appropriate label from note type (`bug` → `bug`, `friction`/`feature` → `enhancement`); (3) GitHub repo configurable in `docs_manifest.yaml` under `github.repo`; (4) token via `GRAIN_GITHUB_TOKEN` env var — never stored in workspace files; (5) prints the created issue URL on success; (6) `grain issue create --title "..." --type bug|feature|friction` as a standalone path that skips the notes log and goes straight to GitHub.
- **Files:** `src/grain/services/github_service.py` (new), `src/grain/cli/notes.py` (extend), `src/grain/cli/report.py` (new), `src/grain/cli/issue.py` (new), tests
- **Model:** frontier_model
- **Dependencies:** P32-T06
- **Note:** implements BOTH the canonical URL-based `grain report` (no token, browser-confirmed, upstream) and the API-based `grain notes publish` (token, headless, files into the user's own repo — the path a familiar/agent can drive without a browser).

### P32-T10 — Docs hygiene — phase_status_consistency audit check + current_focus rewrite
- **Status:** done
- **Description:** Founder-requested hygiene. (1) Rewrite `docs/working/current_focus.md` from 377 lines of self-contradicting per-phase prose to a single Current Phase block + Closed-Phase Ledger; (2) add a `phase_status_consistency` check to `grain docs audit` (error severity) that fires when a phase is described as both active and closed, or when the Current Phase appears in the closed ledger; (3) document the check in `docs_audit_spec.md`.
- **Files:** `src/grain/services/docs_audit_service.py` (extend), `docs/working/current_focus.md` (rewrite), `docs/working/docs_audit_spec.md` (extend), tests
- **Model:** frontier_model
- **Dependencies:** none

---

## Phase 33 — v0.5.0 Planning

> **Status:** ACTIVE (planning) — no execution tasks yet. v0.5.0 scope lives in `docs/working/v0.5.0_contract.md` (DRAFT); this phase locks it into execution phases + packets in a dedicated planning pass, the way Phase 30 planned v0.4.0.

### P33 Notes
- Candidate v0.5.0 deliverables: general-purpose / non-code workspaces, `grain recipe` execution + `recipe suggest`, external signal ingestion, safe apply graduation, Grain-as-engine contract, toolkit contract, dev/runtime alignment, context token-budget proxy, graduated-ceremony / quick lane, package self-update (humans + familiars)
- Locked specs already exist for several: `recipe_spec.md`, `toolkit_contract.md`, `workspace_model.md`, `apply_graduation.md`, `feedback_spec.md`
- Do not start execution until v0.4.0 is released (`pnpm trace release minor`) and the suggest/feedback foundation is stable

---

## Phase 34 — v0.5.0 Recipe Engine (Step-Runner) MVP

> **Status:** ACTIVE (drafted) — 9 packets (P34-T01–P34-T09). First v0.5.0 execution phase: ships the operator-mode recipe step-runner (parser → persistence → engine → CLI → bundled recipe → demo → tests) per `recipe_spec.md` §7 MVP. Critical path is T01–T08 (target July 21); T09 is STRETCH.

### P34 Notes
- Scope is the §7 MVP only: `grain.recipe/v2` parser, file-backed `RecipeRun` (`grain.recipe-run/v1`) under `docs/recipes/runs/<run-id>/`, operator-mode engine, CLI surface, one bundled 6-step research-brief recipe, a pre-staged demo workspace + runbook, and integration tests. Parallel-engine isolation: no `evaluate_workflow_state` / packet-lifecycle coupling.
- **Build order:** T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08; T09 is STRETCH (off the July-21 critical path). The strict numeric dependency graph is acyclic with this topological order.
- **Spec decisions (resolved 2026-06-28):** `supervision` is parsed into `RecipeDefinition` and carried into `run.json`; `start_run` returns outcome `started` (status `pending`, no auto-advance); per-step `gate` is persisted in `run.json`; the service module is `recipe_service.py`; `run.json` separates `mode` (operator|auto) from `supervision` (supervised|gated|autonomous); operator mode pauses at the new `awaiting_input` status — a bare `recipe run` does not auto-complete offline. See `recipe_engine_spec.md` §2.2 / §3.1 / §5.
- **T04↔T06 cycle: resolved** — T04's `recipe list` test uses a scaffolded fixture (not the bundled recipe), recipe enumeration is owned by T03, and T06 depends on T04. Cross-reference labels (T06→T04, T07 dep roles, T08 resume attribution) corrected.
- **Demo approach (locked):** "reference run + live `next`" — show the committed `research-brief-0001` run, then drive `grain recipe next` / `status` live; auto-mode (`--auto`) pre-recorded is the optional "watch artifacts appear" beat.

### P34-T01 — v2 recipe parser + typed dataclasses
- **Status:** done
- **Description:** Parse `grain.recipe/v2` definitions into typed dataclasses (`RecipeDefinition`, `RecipeParam`, steps) with strict-key rejection; validate `category` against `VALID_CATEGORIES`; `supervision` is accept-and-ignore (deferred run-mode), and error messages name the offending key/version.
- **Dependencies:** none

### P34-T02 — File-backed RecipeRun persistence + create_run
- **Status:** done
- **Description:** File-backed `RecipeRun`/`RecipeStepRecord` model (`grain.recipe-run/v1`) with `create_run(...)` and the run-id allocation helper, persisting atomically (step artifact → `run.json`) under `docs/recipes/runs/<run-id>/` for lossless round-trip.
- **Dependencies:** P34-T01

### P34-T03 — Operator-mode recipe engine
- **Status:** done
- **Description:** Operator-mode engine — `resolve` / `start_run` / `next` / `resume` over declared-inputs-only `{{steps.<id>}}` token scoping, with `NextResult` outcomes and typed errors; renders prompts and surfaces output paths, never generating step content.
- **Dependencies:** P34-T01, P34-T02

### P34-T04 — CLI: grain recipe list / show / scaffold
- **Status:** done
- **Description:** `grain recipe list | show | scaffold` over the shared discovery service (bundled + workspace enumeration), with text and `--format json` output; creates and registers the `recipe` Click group.
- **Dependencies:** P34-T01, P34-T03

### P34-T05 — CLI: grain recipe run / next / status / resume / gate
- **Status:** done
- **Description:** Extend the `recipe` Click group with `run | next | status | resume | gate` over the engine, driving operator-mode runs step-by-step and exposing gate approve/reject and resume-on-failure.
- **Dependencies:** P34-T03, P34-T04

### P34-T06 — Bundled research-brief recipe
- **Status:** done
- **Description:** Ship the canonical 6-step, gateless `research-brief` recipe as package data and wire the bundled-recipe discovery enumeration so `grain recipe list/show` (T04) surface it as `source: bundled`.
- **Dependencies:** P34-T01, P34-T03, P34-T04

### P34-T07 — Pre-staged recipe-demo workspace + runbook
- **Status:** done
- **Description:** Pre-staged `examples/recipe-demo/` workspace (a byte-identical copy of the bundled research-brief plus a completed `run.json`) and a shippable runbook for the venue/PyPI demo path, using a valid `supervision` level.
- **Dependencies:** P34-T05, P34-T06

### P34-T08 — Recipe MVP integration / e2e tests
- **Status:** done
- **Description:** Integration/e2e tests over the bundled recipe: operator run-to-`done` (gateless, no API key) and resume-on-failure (engine T03 / CLI T05), discovering the recipe via the engine.
- **Dependencies:** P34-T05, P34-T06

### P34-T09 — Agent auto-mode orchestrator (STRETCH)
- **Status:** done
- **Description:** Auto-mode orchestrator — `resolve_recipe_agent` + a single canonical `workflow_loop.yaml` driving autonomous/gated recipe runs (halting on the gated step) on top of the operator engine; STRETCH, off the July-21 critical path.
- **Dependencies:** P34-T03, P34-T05

## Phase 35 — v0.5.0 Grain-as-Engine Headless Contract (DEFERRED) ✓ CLOSED

> **Status:** CLOSED with 0 tasks executed. The `grain.engine/v1` headless contract was
> planned as 11 packets and never built — no packet produced a `results.md` and none of the
> deliverables (`envelope.py`, `errors.py`, `version.py`, `capabilities.py`) exist in `src/`.
> Phase 36 was begun ahead of it. The scope is intact and deferred to **Phase 37** (v0.6.0);
> the 11 packets moved to `tasks/P37-T*`. Nothing was archived and nothing was dropped.

---

## Phase 36 — v0.5.0 Release Readiness & Fleet Hardening

> **Status:** CLOSING — release-hygiene drafts deferred to Phase 40; `P36-T10` moved to `P37-T12`
> and `P36-T07` merged into `P37-T02` (the Phase 36 notes already said to coordinate, not duplicate).
> Only the three executed packets remain here so the phase can seal.
> **Was:** ACTIVE (drafted) — from the 2026-06-29 grain audit (`docs/working/grain-audit-0.5.0.md`). Closes the finite punch-list between a functionally-working 0.5.0 and a clean public release, fixes the workspace fleet, and lands the user-requested staleness check.
> **Corrections to the audit (founder, 2026-06-29):** (1) `grain-kit` is **already published and owned** on PyPI — the audit's "name taken" CRITICAL is void; the *only* 0.5.0 release blocker is the unpushed `grain-v0.5.0` tag, and tagging/release runs on **GitHub Actions credits that are currently exhausted** (resets later). (2) `packages/{identity-kernel,vault-kit,grimoire}` are **strictly familiar runtime substrate, not grain products** — de-list them from the grain fleet (remove the stray `grain.toml`), do **not** `grain init` them.
> **Sequencing note:** the structured-output/version-resolver items (P36-T06, P36-T09) overlap Phase 37's engine-envelope contract — coordinate, do not duplicate. P37 is the *familiar-facing* envelope layer; these are the plumbing beneath it.

### P36-T01 — Reconcile source version + ship 0.5.0 (tag push credit-blocked)

- **Status:** done — SHIPPED 2026-07-07: grain-kit 0.5.0 live on PyPI (release run 28845125357 all-green: test → build → publish → mirror sync → GH Release). Packet `tasks/P36-T01-TASK-0222/` has full results; operator review then `grain task close`.
- **Description:** `grain doctor` fails 3/4 fleet-wide because the source pyproject version reads `0.1.0` while installed is `0.5.0`. Confirm the true on-disk `version`, fix so doctor passes everywhere. Then ship 0.5.0 via the repo convention (`pnpm trace release` / push `grain-v0.5.0`) — **the release pipeline only fires on tag push and has never run for 0.5.0; blocked until Actions credits reset.** Name is fine (`grain-kit` already published).
- **Dependencies:** none

### P36-T14 — Close the assay bridge loop: surface review findings on ingest

- **Status:** done — packet `tasks/P36-T14-TASK-0223/`. Live round trip (2026-07-07) proved the bridge works end-to-end incl. `code_review`; this task adds what was missing: `review.findings` + `followup_candidates` rendered into results.md and the review block persisted in verification_result.json. TDD, 2 new tests, 1634 green.
- **Description:** `grain verify ingest` existed (Phase 28) but dropped assay's structured review findings on the floor — only the summary reached the packet. Render `file:line [severity] message` findings and `follow-up:` lines; persist `review` in the result record. Out of scope: FR-006 workflow-gate wiring.
- **Files:** `src/grain/services/verification_service.py`, `tests/test_verify_submit_cmd.py`
- **Dependencies:** none

### P36-T15 — FR-006 verification gate in workflow evaluator

- **Status:** done — packet `tasks/P36-T15-TASK-0224/`. Machine-readable gate: `verification_pending`/`verification_failed` stop reasons keyed off verification_request.json, `verification_id` on the evaluation, failure summary + follow-ups in blocking_reasons, exact ingest resume command. Live-verified full lifecycle via CLI. TDD, 3 new tests, 1637 green.
- **Description:** Closure validation already blocked on pending/failed verification but agents only saw generic `review_close_blocked`. Implements the v2-plan FR-006 machine contract in the read-only evaluator (no status auto-mutation — guidance instead, to avoid backlog-sync drift).
- **Files:** `src/grain/domain/workflow.py`, `src/grain/services/workflow_service.py`, `tests/test_workflow_state_service.py`
- **Dependencies:** P36-T14

---

## Phase 37 — v0.6.0 Grain-as-Engine Headless Contract

> **Status:** ACTIVE (drafted) — 20 packets (P37-T01–P37-T20). T01–T12 ship the *machine interface*; T13–T20 ship the *workflow contract and state kernel* that Diwa's Missions targets (`docs/superpowers/specs/2026-07-09-entity-boundaries-design.md` §5.1, §9). Ships the headless engine contract: `grain.engine/v1` envelope + typed error model, single version resolver, capability registry, envelope/error wiring across CLI + MCP surfaces, and a CLI↔MCP conformance suite. Foundation T01–T03 land first; per `engine_contract_spec.md` §8. The 11 packets map 1:1 onto the §8 MVP areas.

### P37 Notes
- **Build order:** foundation T01 / T02 / T03 (no deps, parallelizable) → T04, T05 (consume T01) → T06 (consumes T01/T02/T03/T05) → T07, T08 → T09, T10 → T11 (capstone, consumes T01–T10). The declared graph is acyclic with this topological order.
- **Scope is §8 MVP only:** envelope + errors, version resolver, capability registry, envelope wiring (workflow `next`/`run`/`loop`/`explain` + recipe sites), recipe error mapping, MCP surface expansion, HTTP wrapper fix, capabilities/workspace CLI, non-interactive gate envelopes, version check, and conformance tests. **Deferred per §8:** `workflow guard`/`reconcile` and the remaining legacy JSON sites (task*/review*/suggest*/docs audit/status) stay bare-by-default behind `--envelope`/`GRAIN_ENGINE_ENVELOPE=1`.
- **Cross-packet items to resolve before building (see verify report):** (1) `version_check` ownership across T03 (capability seed) / T06 (MCP tool) / T10 (CLI + service) — T10 must consume, not re-add; (2) pin the T03 seed `surfaces` values so T06's `tools/list` derivation is deterministic; (3) have T01 enumerate the `suggest accept` / `docs audit` kinds in `VALID_ENGINE_KINDS` so T09 does not hit its escalation/blocker path; (4) state that T09's new suggest/docs emits are always-enveloped to reconcile with T04's default-bare legacy sites.

### P37-T01 — grain.engine/v1 envelope + typed error model

- **Status:** draft
- **Description:** Define the `grain.engine/v1` `EngineEnvelope` and `ErrorEnvelope` dataclasses (§4.2), `VALID_ENGINE_KINDS`/`VALID_ERROR_CODES`, and the error taxonomy (`code`/`exit_code` as ClassVars on `ForgeError` subclasses) plus a format-aware `error_handler`; `errors.py` and `envelope.py` resolve one-way (acyclic) and an `envelope_to_dict` serializes the error object.
- **Dependencies:** none

### P37-T02 — single version resolver (src/grain/version.py)

- **Status:** draft
- **Description:** Introduce one `get_version()` resolver in `src/grain/version.py` (via `importlib.metadata`) and rewire reported-version sites (MCP `serverInfo.version`, etc.) to it, removing scattered `MAJOR.MINOR.PATCH(-dev)` string literals as reported versions.
- **Dependencies:** none
- **Absorbed from P36-T07:** `cli/__init__.py` chains three version checks using two manifest keys for the same concept (`project.minimum_grain_version` vs `upgrade_policy.min_version` — dual source of truth), one of which runs a full filesystem dry-run scan on *every* invocation, all wrapped in silent `except: return`. Collapse to one function, one key, off the hot path; let failures surface. Land on P37-T02's single resolver.

### P37-T03 — capability registry (Capability dataclass + CAPABILITIES seed)

- **Status:** draft
- **Description:** Frozen `Capability` dataclass with `__post_init__`/`VALID_*` validation and the `CAPABILITIES` seed (§6.2) carrying `since`/`kind`/`drive`/`stability`/`surfaces`; pins the §6.2 ids and the genuinely-frozen kind/drive/stability subset, including per-entry `surfaces ∈ {cli, mcp}`.
- **Dependencies:** none

### P37-T04 — envelope + error wiring across CLI emit sites

- **Status:** draft
- **Description:** Route `workflow next`/`run`/`loop`/`explain` and the recipe CLI sites through a single `emit(...)` helper that frames the `grain.engine/v1` envelope (built inline per T01's note) with `grain_version` from the version resolver, behind the `--envelope`/`GRAIN_ENGINE_ENVELOPE=1` opt-in; `guard`/`reconcile` are deferred per §8.
- **Dependencies:** P37-T01, P37-T02

### P37-T05 — engine_error_to_forge mapping for recipe engine

- **Status:** draft
- **Description:** Extract `engine_error_to_forge(exc) -> ForgeError` mapping recipe engine errors (§4.3 table) and collapse `_drive` to catch both `RecipeEngineError` and `RecipeSchemaError` (a `ValueError`, not a `RecipeEngineError`), preserving today's exit codes (e.g. `RecipeSchemaError` → exit 3) with no behavior change.
- **Dependencies:** P37-T01

### P37-T06 — MCP surface expansion (catalog-driven tools/list)

- **Status:** draft
- **Description:** Expand `mcp_service.py` to a single capability-derived catalog — `tools/list` filtered by `surfaces ∈ mcp`, `_ok`/`_err` envelope helpers, and the extended `McpTool` (write/capability) — with every catalog tool delegating to the CLI-canonical service fn and returning a `grain.engine/v1` envelope; defers the `version_check` tool to T10.
- **Dependencies:** P37-T01, P37-T02, P37-T03, P37-T05

### P37-T07 — HTTP MCP wrapper alignment (apps/grain-mcp/main.py)

- **Status:** draft
- **Description:** Align the HTTP wrapper app (`apps/grain-mcp/main.py`, at monorepo root) so `tools/list` derives from the expanded registry and JSON-RPC boundary errors map to the §4 error shape (§5.6); resolve the cross-package path/test-runner/REUSE-header questions before editing.
- **Dependencies:** P37-T01, P37-T02, P37-T06

### P37-T08 — CLI: grain capabilities / workspace

- **Status:** draft
- **Description:** `grain capabilities list|show` and `grain workspace list` commands emitting `grain.engine/v1` envelopes (status `ok`/`error`) over the capability registry; consumes the envelope/error taxonomy (T01), version resolver (T02), and `CAPABILITIES` (T03).
- **Dependencies:** P37-T01, P37-T02, P37-T03

### P37-T09 — non-interactive gate/ok envelopes (suggest accept, docs audit)

- **Status:** draft
- **Description:** Emit `grain.engine/v1` envelopes on the consent path for `suggest accept` and `docs audit` (§7.1) — `status:gate` on the gate, `status:ok` on `--yes` — always-enveloped on these legacy sites regardless of the default-bare opt-out; depends on T01 having registered their kinds.
- **Dependencies:** P37-T01, P37-T04

### P37-T10 — version check (grain version --check/--refresh + version_check tool)

- **Status:** draft
- **Description:** `grain version` with `--check`/`--refresh` plus a shared `version_service` producing the `grain.version/v1` payload (installed/latest/update_available via the pypi adapter, §7.2) that both the CLI and the MCP `version_check` read tool delegate to; consumes (not re-adds) the T03 capability seed and T06 MCP helpers. Network is the §2 principle-4 carve-out.
- **Dependencies:** P37-T01, P37-T02, P37-T03, P37-T06

### P37-T11 — change proposal + CLI↔MCP conformance tests

- **Status:** draft
- **Description:** Capstone: the canonical-doc change proposal plus the conformance suite — taxonomy error round-trip and CLI↔MCP frame parity over an always-enveloped command pair (e.g. CLI `capabilities` ↔ MCP `capabilities_list`, or CLI `version` ↔ MCP `version_check`), not the default-bare legacy `workflow`/`recipe` sites.
- **Dependencies:** P37-T01, P37-T02, P37-T03, P37-T04, P37-T05, P37-T06, P37-T07, P37-T08, P37-T09, P37-T10

---

### P37-T12 — @grain_command decorator + structured-output contract migration

- **Status:** draft
- **Description:** Introduce a `@grain_command`/`@pass_repo` decorator (kills ~238 repeated `repo/fmt` boilerplate copies + 108 ad-hoc `resolve_repo_root` calls) and migrate all CLI modules onto `print_result/CommandResult` (only 7/31 use it today; 813 hand-rolled `click.echo`). Makes `--format json` a real contract — **the machine/MCP interface familiars depend on** (audit Positioning). Coordinate tightly with Phase 37: the engine envelope is the outer familiar-facing layer; this is the per-command output contract beneath it. Large — split before execution.
- **Dependencies:** P37-T01, P37-T04 (coordinate)
- **Moved from:** P36-T10 (ROADMAP.md:94 calls this Phase 37's plumbing).

### P37-T13 — contracts/workflow.py — the typed workflow vocabulary
- **Status:** done
- **Description:** Populate `src/grain/contracts/` (today an 82-byte license header) with spec §5.1's five terms as TYPES ONLY: enums `Gate`/`RunStatus`/`StepStatus`/`Mode`/`Supervision`/`StopReason`, and frozen dataclasses `Artifact`/`StepSpec`/`Protocol`/`StepRecord`/`Run` with `to_dict`/`from_dict`. No reducer, no port, no I/O, stdlib only. Do **not** wire it into `grain/__init__.py`.
- **Acceptance:** `python -c "import grain.contracts.workflow"` succeeds; an import-trace test proves `import grain.cli` does NOT pull `grain.contracts`, so `grain status` startup is untouched; enum values are byte-equal to the `VALID_*` frozensets in `domain/recipe_run.py:28-42`; `StopReason` members match a captured roster of the ~20 literals in `services/workflow_service.py` (the test asserts the roster, invents nothing); `Run.from_dict(run.to_dict())` is identity. **Corrected 2026-07-09:** byte-identical round-trip of a recipe `run.json` is NOT achievable here and moved to `P37-T17` — `RecipeRun.to_dict` emits `recipe`/`recipe_apiVersion` under `grain.recipe-run/v1`, while the contract speaks of a `protocol` under `grain.workflow-run/v1`. T17 owns that mapping.
- **Demo:** SAFE pre-demo — new file, off the CLI startup import graph.
- **Dependencies:** none

### P37-T14 — engine/kernel.py — RunStore port + pure advance() reducer
- **Status:** review
- **Description:** New leaf module `src/grain/engine/kernel.py` (NOT `contracts/` — see P37-T20): the `RunStore` Protocol, `Event`/`Effect`/`Transition`, and `advance(run, event, *, now, max_attempts) -> Transition`. `advance()` is pure and returns Effects the driver applies — this is how the reject transition survives: it emits a `DiscardArtifact` effect rather than unlinking. `RunStore` MUST expose `discard_artifact()` (the load-bearing delete at `services/recipe_service.py:739`), `save(run, *, expected_version)` with a `ConcurrentModification` error, and `list_runs()` ordered by a `created` timestamp — never lexical id sort.
- **Acceptance:** Property tests: reject yields `DiscardArtifact` + `StepRecord.artifact=None`; `advance()` performs zero I/O (asserted with a spy RunStore that raises on any call); `step_failed` increments attempts exactly once and flips FAILED only at `attempts >= max_attempts`; a REVIEW gate halts at `AWAITING_GATE`. A test asserts `grain.engine.kernel` imports no `grain.services`, `grain.domain`, or `os.path`.
- **Demo:** SAFE pre-demo — new module, off the startup graph.
- **Dependencies:** P37-T13

### P37-T15 — engine/fs_store.py — FilesystemRunStore + store-agnostic conformance suite
- **Status:** draft
- **Description:** Implement `RunStore` over the exact `recipe_store.py` layout: `docs/recipes/runs/<id>/run.json`, temp+`os.replace` atomic write (`recipe_store.py:52-62`), artifact-then-run ordering (`:177-211`). `discard_artifact` mirrors the unlink at `recipe_service.py:739`; `expected_version` via mtime/etag; `list_runs` newest-first via `Run.created`. Ship a store-agnostic conformance suite that Diwa's Postgres store must also pass. Leave `recipe_store.py` untouched — `fs_store.py` is dead to the CLI until P37-T17.
- **Acceptance:** Conformance suite green against `FilesystemRunStore`; a run written by `fs_store` loads byte-identically through the existing `recipe_store.load_run`; a save with a stale `expected_version` raises `ConcurrentModification`.
- **Demo:** SAFE pre-demo — new module, not imported by `cli/recipe.py`.
- **Dependencies:** P37-T14

### P37-T16 — Characterize the recipe engine's real transitions as golden fixtures
- **Status:** draft
- **Description:** Test-only capture of what the refactor must preserve: operator reject deletes the on-disk artifact and completion is decided by `_artifact_present_nonempty(output_path)` (`recipe_service.py:340, 569-581, 737-744`); the operator-vs-auto attempts divergence (once-per-pause guard `:592-594` vs per-invocation `:820`); and the driver outcome set `VALID_NEXT_OUTCOMES` (`:71-80`).
- **Acceptance:** A characterization suite pins current `grain recipe run` operator and auto flows — including reject re-arm and no re-fire — and passes against unmodified `main`.
- **Demo:** SAFE pre-demo — tests only.
- **Dependencies:** none

### P37-T17 — Swap recipe_store.py + recipe_run.py onto the contract
- **Status:** draft
- **Description:** Recast `services/recipe_store.py` to delegate to `FilesystemRunStore`; retype `domain/recipe_run.py` onto the contract vocabulary (`VALID_*` frozensets -> `set(RunStatus)` etc., `gate: Gate`, `artifact: Artifact | None`), keeping `to_dict` byte-identical so live `run.json` files still load.
- **Acceptance:** P37-T15 conformance and P37-T16 characterization suites both pass; `to_dict` of a migrated `RecipeRun` equals the captured pre-migration JSON byte-for-byte.
- **Demo:** DEMO-PATH — `recipe_store.py`/`recipe_run.py` are imported at CLI startup (`cli/__init__.py:52 -> cli/recipe.py:43-52 -> recipe_store.py:36-37`). `cli()` wraps only `main()` (`cli/__init__.py:317-334`), so an import fault here is an uncatchable traceback on `grain status`, the demo's first command. Requires a green `grain status` smoke test before the demo.
- **Inherited from P37-T13:** own the on-disk compatibility mapping — `to_dict` of a migrated `RecipeRun` must equal the captured pre-migration `run.json` byte-for-byte.
- **Dependencies:** P37-T15, P37-T16

### P37-T18 — Refactor recipe_service.py onto RunStore + advance()
- **Status:** draft
- **Description:** Replace inline cursor/gate/status transitions and the `recipe_store._utc_now` private reach-ins (`:596,634,704,824,929`) with an injected `RunStore` + `advance()`. Reconcile operator and auto so each failed attempt emits exactly one `step_failed` event. Route reject's unlink through the `DiscardArtifact` effect. Keep recipe.yaml resolution, prompt render and subprocess (`:886`) in the service — those are driver concerns. `VALID_NEXT_OUTCOMES` stays the driver's vocabulary; do **not** map it to `StopReason` (the recipe engine has no stop_reason).
- **Acceptance:** P37-T16 characterization suite passes unchanged; a golden test asserts `grain recipe run` stdout is byte-identical pre/post for one operator and one auto recipe.
- **Demo:** DEMO-PATH — on the startup graph. Note `grain recipe run` is explicitly NOT demoed (`docs/working/demo_runbook.md:43, :170-172`), so the risk is import-time, not behavioural.
- **Dependencies:** P37-T17, P37-T14

### P37-T19 — Type workflow_service.py stop_reason as StopReason
- **Status:** draft
- **Description:** Change `WorkflowEvaluation.stop_reason` from a bare `str` to `StopReason` and migrate the ~20 inline literal comparisons 1:1. This is `StopReason`'s only production caller.
- **Acceptance:** `grain workflow next` and `grain --format json workflow next` emit byte-identical text and JSON pre/post (golden test).
- **Demo:** DEMO-PATH, HIGHEST RISK — `workflow_service.py` backs `grain workflow next`, demo Beats 2 and 5 including the marquee JSON-envelope beat (`demo_runbook.md:59, :116`).
- **Dependencies:** P37-T13

### P37-T20 — Governance change proposals for contract scope and the §9 exit
- **Status:** draft
- **Description:** Author change-proposal notes (do NOT edit locked canonical docs directly): (1) §5.1/§11 authorize a five-term *vocabulary*, and §11 says contracts "shares types, not code" — `advance()` and `RunStore` are code, which is why they live in `grain/engine/`; propose ratifying that surface. (2) §9's exit criterion is not fully met: this phase extracts the state core but not a standalone `grain-core` distributable, and Diwa's executor is permanent. (3) `capability_register.md` assigns "runs" to Grain while §2 says two products implementing one capability means one is wrong — propose splitting the single-authored state machine from per-product drivers. (4) Record the founder's override of §9's "Grain is not touched before the July demo". (5) Record the reversal of P36-T13's "delete `src/grain/contracts/`".
- **Acceptance:** A proposals doc under `docs/working/` enumerating the five items with target file + section.
- **Demo:** SAFE pre-demo — docs only.
- **Dependencies:** none

### P37-T21 — Extract grain-contracts as a zero-dependency distribution
- **Status:** done
- **Description:** `grain-kit` mandatorily depends on `networkx`, `textual`, `pdfplumber`, `openpyxl`, `python-docx` and `tree-sitter-language-pack`. Diwa is a FastAPI service that needs six enums and five dataclasses. Ship the vocabulary as its own zero-dep distribution (`packages/grain-contracts`, importable as `grain_contracts`); `grain.contracts.workflow` re-exports it so spec §5.1's address still holds. This is the first slice of the storage-agnostic `grain-core` that §9 names as the exit criterion for Diwa's temporary Missions runtime.
- **Acceptance:** `importlib.metadata.requires("grain-contracts")` has no runtime entries; `grain.contracts.workflow.Run is grain_contracts.workflow.Run`; `import grain.cli` pulls neither module; grain's suite green; `grain status` exits 0.
- **Demo:** SAFE pre-demo — new package; `grain/contracts/workflow.py` stays off the CLI startup graph.
- **Release blocker:** `grain-contracts` must be published to PyPI **before** `grain-kit` 0.6.0, or the release ships an uninstallable package (`release-python.yml` publishes grain-kit only). See tooling note #10.
- **Dependencies:** P37-T13

---

## Phase 38 — Tooling Friction Remediation

> **Process deviation (recorded 2026-07-09):** this phase was executed as commits (`c917cb7`, `f63716d`) **without task packets**, so `grain workflow reconcile` reports 11 `missing_packet` warnings for T01–T10 and T12. The statuses are accurate; the packets never existed. `reconcile --fix` cannot express "shipped without a packet" — filed as tooling friction.
> **Status:** DRAFT — sourced from a fleet-wide sweep of `docs/working/tooling_notes.md` across
> 12 unique Grain workspaces (2026-07-09). 87 entries harvested, 75 open, 65 against Grain,
> 61 unique after dedupe. Each was **reproduced against the published grain-kit 0.6.0** in a
> throwaway workspace before earning a task; 29 no longer reproduce and are listed for closure
> in `docs/working/friction_sweep_2026-07-09.md`, not fixed here.

### P38 Notes
- **The inbox is a fleet property, not a repo property.** The same defect ("`--format` only
  works globally", "onboard leaves `proposals/` missing") was independently logged in
  Diwata-Labs root, assay, aether, and Limitless — four repos, one bug, four uncoordinated
  notes. A per-repo inbox structurally cannot dedupe that. T10 is the fix; everything else is
  a symptom.
- **Build order:** T01–T04 are cheap and independently shippable. T05–T09 are the workflow
  engine and can proceed in parallel. T10 and T11 close the loop and should land last.
- Do **not** re-file the six defects fixed in 0.6.0 (`orchestrate` ×2, `init`/`onboard` health,
  `status` task counting, `reconcile` phase blindness, `phase close --allow-empty`).

### P38-T01 — `grain onboard` must scaffold `docs/working/proposals/`
- **Status:** done
- **Description:** `grain onboard .` produces a workspace that immediately fails `grain docs validate` with exit 3: `Doc 'proposals': expected path not found: docs/working/proposals/`. `grain init` creates the directory; `onboard`'s `_REQUIRED_DIRS` omits it. This is the third instance of the same init/onboard desync (the seed-file list and the prompt list were reconciled in 0.6.0; the directory list was not). Add `docs/working/proposals` to onboard, then factor **one shared constant** the two scaffolders both consume so they cannot drift a fourth time. Regression test: `grain docs validate` exits 0 on a freshly onboarded repo.
- **Repro:** `mkdir /tmp/x && cd /tmp/x && git init -q . && grain onboard . && grain docs validate` → exit 3.
- **Files:** `src/grain/services/onboard_service.py`, `src/grain/services/init_service.py`, `tests/test_onboard_cmd.py`
- **Dependencies:** none
- **Effort:** trivial

### P38-T02 — Accept `--format` after the subcommand, everywhere
- **Status:** done
- **Description:** `--format` is a group-level option, so `grain task list --format json` and `grain workflow next --format json` both die at Click parsing with exit 2 (`No such option '--format'`), while `grain --format json task list` succeeds. Exactly two commands declare a local `--format` — `onboard` and `upgrade` — so an agent that learns the flag on one of those and applies it anywhere else gets a usage error. Attach an eager `--format [text|json]` to every envelope-emitting leaf command (a shared decorator or `Group` subclass), deferring to the top-level value when unset. Grain is agent-first; a flag whose position matters is a trap.
- **Repro:** `grain task list --format json` → exit 2; `grain --format json task list` → exit 0. Local `--format` grep: only `cli/onboard.py:20` and `cli/upgrade.py:22`.
- **Files:** `src/grain/cli/__init__.py`, and every module under `src/grain/cli/`
- **Dependencies:** none
- **Effort:** hours

### P38-T03 — Machine-readable output fidelity
- **Status:** done
- **Description:** Four output bugs that make Grain lie to the agent parsing it. (1) `grain upgrade --add-missing` prints `Added:` / `- (none)` while actually writing the files — `_scan_absent_seeded_files` appends to `result.absent` and never to `result.added`. (2) The `N Grain-managed file(s) are out of date` hint never clears after `grain upgrade` skips locally-customized files, because the stale count includes `skipped_customized`. (3) That hint prints to stderr even under `grain --format json`, unlike the sibling version gate. (4) `grain --format json phase close --dry-run` returns `"dry_run": false` on early-return paths.
- **Repro:** in a fresh `grain init` workspace, `rm docs/working/tooling_notes.md prompts/tasks.review.md && grain upgrade --add-missing` prints `Added:` `- (none)` yet both files exist afterwards.
- **Files:** `src/grain/services/upgrade_service.py`, `src/grain/cli/__init__.py`, `src/grain/services/phase_close_service.py`
- **Dependencies:** none
- **Effort:** hours

### P38-T04 — `grain phase list` and `grain phase status`
- **Status:** done
- **Description:** `grain phase` exposes only `archive`, `close`, `next`. There is no CLI way to see all phases and their status — `grain phase list` and `grain phase status` both exit 2 with `No such command`. The nearest command, `phase next`, sounds mutating but is read-only. Add `phase list` (every `## Phase N —` heading with its `> **Status:**` and a done/ready/total rollup) and `phase status` (read-only view of the active phase), reusing the existing phase parser. Both honor `--format json` (see T02).
- **Repro:** `grain phase list` → exit 2. `grain phase --help` shows only archive/close/next.
- **Files:** `src/grain/cli/phase.py`
- **Dependencies:** P38-T02
- **Effort:** hours

### P38-T05 — First-class review approval
- **Status:** done
- **Description:** `grain task close` refuses unless `user_review_state == 'approved'` (`validators/packet_validator.py:118`), but **no CLI command sets that state.** `review` offers check/handoff/summary; `verify` offers ingest/status/submit; neither writes approval. The only path to a validated close is hand-editing the `## User Review` → `- **State:**` field in `results.md`. This was hit for real on 2026-07-09 closing TASK-0222/0223/0224. Add `grain review approve --id <TASK> --summary "..."` (and `--reject`), writing the block Grain already parses. The human gate is Grain's headline feature; it should not be reachable only by hand-editing markdown.
- **Repro:** `grain task close --id TASK-0001` on a reviewed packet → `user review state must be 'approved' before closing to 'done'`; `grep -ri approv src/grain/cli/review.py` finds no setter.
- **Files:** `src/grain/cli/review.py`, `src/grain/services/review_service.py`, `src/grain/domain/review_bundle.py`
- **Dependencies:** none
- **Effort:** hours

### P38-T06 — Task CLI ergonomics: positional IDs and `grain task start`
- **Status:** done
- **Description:** The `task` group is flag-only and rejects the natural forms. `grain task show P8-T02-TASK-0001` → `Missing option '--id'`; `grain task validate P8-T02-TASK-0001` → `Got unexpected extra argument` — even though the packet dir name is exactly what `grain task list` prints. Accept an optional positional (TASK-#### or packet dir) across show/validate/status/prepare/close, keeping `--id`. Separately, `grain task status --id X --status in_progress` is rejected (the legal path is draft→ready→in_progress) and, when it does apply, updates only the packet's `task.md`, leaving `backlog.md` and `current_task.md` drifted until `reconcile` warns. Add `grain task start <id>` that performs the whole legal transition and syncs both working docs, and make the rejection name the legal next hop.
- **Repro:** `grain task show P1-T01-TASK-0001` → exit 2, `Missing option '--id'`.
- **Files:** `src/grain/cli/task.py`, `src/grain/services/task_service.py`
- **Dependencies:** none
- **Effort:** days

### P38-T07 — Focus-doc phase parsing is brittle, and reconcile can't repair it
- **Status:** done
- **Description:** `grain workflow next` hard-blocks with `required_docs_invalid` ("unable to parse current phase") when `## Current Phase` uses a hyphen, en-dash, or colon instead of the em-dash the regex demands (`_CURRENT_PHASE_LINE`, `workflow_service.py:48`) — a routine by-product of hand-editing. `grain workflow explain` then routes the agent to `grain workflow reconcile`, which reports `issues 0` and cannot repair it, so the guidance dead-ends. Loosen the separator to `^Phase\s+(\d+)\s*[—–:-]` and add a reconcile `focus_phase_parseable` check that flags and repairs the malformed line.
- **Repro:** set the heading to `Phase 1 - Foundation`; `grain workflow next` → `required_docs_invalid`; `grain workflow reconcile` → `issues 0`.
- **Files:** `src/grain/services/workflow_service.py`, `src/grain/services/reconcile_service.py`
- **Dependencies:** none
- **Effort:** hours

### P38-T08 — Phase-close gate is off below phase 16; orphan packets undetected
- **Status:** done
- **Description:** Two gaps in the same layer. (1) The `previous_phase_not_closed` gate is disabled below phase 16 by `_PHASE_CLOSE_MIN_ENFORCED = 15` (`workflow_service.py:59`), so every project in phases 1–14 — which is every project that adopts Grain — can hand-edit `current_focus.md` past an unclosed phase with no gate. Make the threshold per-repo (stamp it at `init`) or lower it to 1 for fresh workspaces. (2) `reconcile` skips backlog tasks marked `done`/`in_progress` that have no packet directory (`if packet_dir is None: continue`), and never notices deliverable artifacts on disk with no backing packet. Invert the skip into a report-only `missing_packet` finding.
- **Repro:** Phase 1 done, `current_focus.md` hand-edited to Phase 2 with no `Phase 1 closed:` marker → routes straight into P2-T01. Same setup at phases 15/16 correctly stops.
- **Files:** `src/grain/services/workflow_service.py`, `src/grain/services/reconcile_service.py`, `src/grain/services/init_service.py`
- **Dependencies:** none
- **Effort:** hours

### P38-T09 — Legacy-packet validation escape hatch
- **Status:** done
- **Description:** `grain task validate --all` hard-fails (exit 3) on a legacy packet holding `task.md` + `context.md` but missing `plan.md`/`deliverable_spec.md`. The simple-packet exemption only covers packets with **zero** planning files, so a partial legacy packet can never pass, and the `- **Mode:** simple` field that `grain task create --simple` writes is ignored by the validator. Pick one: honor `Mode: simple`, add `grain task backfill <id>` to seed missing files from templates, or add `--skip <id>`. Onboarding an existing repo currently means a manual rewrite with no migration path.
- **Repro:** create a packet, `rm plan.md deliverable_spec.md`, `grain task validate --all` → exit 3.
- **Files:** `src/grain/validators/packet_validator.py`, `src/grain/cli/task.py`
- **Dependencies:** none
- **Effort:** hours

### P38-T10 — Make the friction inbox self-draining: `grain notes triage` and fleet mode
- **Status:** done
- **Description:** The writer and reader both exist — `grain notes add|list|show|resolve|publish` all work in 0.6.0 (the `grain notes add` note is stale). What is missing is anything that **closes the loop**: nothing re-checks whether an open note still reproduces, so more than half this fleet's inbox is fixed-but-never-closed. Add `grain notes triage`, which for each open note replays its recorded `command` (or hands it to an agent) and flags notes whose symptom no longer reproduces as closure candidates. Then add **fleet mode**: `grain notes --fleet <roots...>` scans a set of workspaces, normalizes by `command` + `category`, and emits one finding with N `seen_in` workspaces — exactly the rollup this sweep was hand-built to produce. `grain notes publish --fleet` then files one deduplicated issue per real defect instead of four.
- **Repro:** 61 unique frictions across 12 workspaces; 29 no longer reproduce. The same four defects were logged independently in four repos.
- **Files:** `src/grain/cli/notes.py`, `src/grain/services/notes_service.py`
- **Dependencies:** P38-T02
- **Effort:** days

### P38-T12 — `grain notes triage` classification is unsound: exit code is not evidence
- **Status:** done
- **Description:** Triage marks a note stale when its recorded command now exits 0 in a pristine throwaway workspace. Measured against the real fleet on 2026-07-09 that rule has **~27% precision (4 of 15 stale candidates sound) and poor recall** — it reports `grain task close` and `grain notes add` as *still open* although both were fixed, because a bare invocation exits 2 for a missing argument. Two independent defects, one root cause — *an exit code is not evidence*.
  **(a) State-independence.** Replaying a bare command in an empty workspace exits 0 whether or not the note's symptom was fixed, because the symptom needed state the sandbox does not have. Verified by installing grain-kit 0.5.0 in an isolated venv and replaying each candidate: `onboard .`, `upgrade`, `upgrade --diff`, `upgrade --add-missing`, `doctor`, `phase next`, `workflow next`, `task validate` and `--format json workflow next` **all exit 0 on 0.5.0 too**. Only `task list --format json`, `workflow next --format json`, `phase list` and `phase status` exited 2 on 0.5.0 and 0 on 0.6.0 — the four whose symptom lived on the CLI surface.
  **(b) Exit-2 ambiguity.** Click exits 2 for both `No such command 'frobnicate'` and `Missing argument 'MESSAGE'`. So ``grain notes add`` — stale, because the command shipped — replays as `exit=2` and stays open. The note that motivated this entire phase is the one case the heuristic cannot see.
  **Fix.** Stop classifying on exit code alone. Auto-classify stale ONLY when the symptom is state-independent, i.e. the recorded command's stderr on an older grain matches a CLI-surface signature (`No such command`, `No such option`, `Got unexpected extra argument`, `Missing option`) and the current version no longer produces it. Everything else routes to `needs human`, which is honest. Optionally support `--baseline <version>` to install and replay against the version the note was filed against; without a baseline, refuse to call anything stale that is not a CLI-surface symptom. And never let `--resolve-stale` act on a candidate the tool cannot justify.
- **Repro:** `grain notes triage --fleet <9 roots>` reports `15 stale · 7 open · 27 human`. `uv pip install grain-kit==0.5.0` then replay: 11 of the 15 already exit 0 on 0.5.0. `grain notes add` -> exit 2 `Missing argument`; `grain notes frobnicate` -> exit 2 `No such command`.
- **Files:** `src/grain/services/notes_service.py`, `tests/test_notes_triage.py`
- **Dependencies:** P38-T10
- **Effort:** hours

### P38-T11 — Drain the fleet inbox
- **Status:** draft
- **Description:** Close the 29 verified-stale notes across the 12 workspaces, citing the version that fixed each. Blocked on **T12**, not T10: triage as shipped has ~27% precision, so `--resolve-stale` would close 11 notes it cannot justify. Drain by hand, or wait for a sound classifier. Also reconcile the two Limitless trees: `~/Limitless` and `~/Documents/Limitless` hold **different** `tooling_notes.md` content, and `~/Limitless-wt/{stg,pg-lift,crm-backfill}` are byte-identical worktree copies whose inboxes will diverge the moment anyone writes to one.
- **Dependencies:** P38-T12
- **Effort:** hours

---

## Backlog Maintenance Rules

1. Backlog items must remain concrete and implementable
2. Backlog items should map to one or more future task packets
3. Large backlog items may be split before execution
4. Backlog items must not redefine canonical rules
5. Closed phases are collapsed to a stub entry — verbose task descriptions live in the task archive


## Phase 40 — Release Hygiene & DX

> **Status:** DRAFT — the release-hygiene half of Phase 36, deferred so Phase 36 could seal and the
> engine-contract work in Phase 37 could become reachable by `grain phase next`. Nothing here is new
> scope; every task is a Phase 36 draft carried over verbatim, renumbered.

### P40 Notes
- Carried over from Phase 36 on 2026-07-09. `P36-T10` went to `P37-T12` and `P36-T07` was absorbed by
  `P37-T02` instead, per Phase 36's own sequencing note.
- `P40-T10` (was `P36-T13`) has one bullet struck: deleting `src/grain/contracts/`. That package is
  unbuilt, not dead — spec §5.1 reserves it, and `P37-T13` populates it.

### P40-T01 — Split 6 heavy lazy deps into extras

- **Status:** draft
- **Description:** Move `textual`, `pdfplumber`, `python-docx`, `openpyxl`, `networkx`, `tree-sitter`(+`-language-pack`) from mandatory deps (`pyproject.toml:30-40`) into extras (`[tui]`/`[office]`/`[scan]`). All are already lazy-imported with fallbacks → runtime cost ≈ 0, install footprint drops massively (tree-sitter-language-pack alone is hundreds of MB). Add helpful `pip install …[office]` ImportError messages. Extras pattern exists at `pyproject.toml:45-57`. (Ships in the next minor since it changes the published dep surface.)
- **Dependencies:** none
- **Carried from:** P36-T02

### P40-T02 — Fix pyproject [project.urls]

- **Status:** draft
- **Description:** Homepage/Repository/Issues point at `Diwata-Labs/Grain` but the public mirror is `Diwata-Domains/Grain` → 404 links in immutable PyPI metadata. Fix before the next publish.
- **Dependencies:** none
- **Carried from:** P36-T03

### P40-T03 — Release pre-flight (clean dist/, twine check)

- **Status:** draft
- **Description:** Drop the stale `grain_kit-0.4.0-py3-none-any.whl` from `dist/` (a manual `uv publish`/`gh release … dist/*` would ship 0.4.0), and wire `uv sync --extra release && twine check dist/*` so README long-description rendering is validated before upload (the `release` extra is declared but not installed today).
- **Dependencies:** P36-T02
- **Carried from:** P36-T04

### P40-T04 — Remove orphaned products/grain/uv.lock

- **Status:** draft
- **Description:** `products/grain/uv.lock` pins `grain-kit 0.1.7` (vs pyproject 0.5.0) and drives `release-python.yml`'s cache key, so release resolves differently from CI (which uses the root lock). Delete/regenerate and point the release cache glob at the root lock.
- **Dependencies:** none
- **Carried from:** P36-T05

### P40-T05 — Workspace staleness check (the requested feature)

- **Status:** draft
- **Description:** Add `check_staleness(root, installed_version) -> StalenessReport` to `upgrade_service.py` (reuse `load_upgrade_policy` + `upgrade_repo(dry_run=True)`); **pair version comparison with the file-drift scan** (the `min_version` ratchet bumps unconditionally, so a pure version check goes quiet while customized files stay stale). Wire into `doctor` (new `workspace_current` check + "Upgrade" section) and a one-line `status` warn. **Fix the silent no-op nag loop:** report stale-applyable vs `customized_skipped` separately and route the latter to `grain upgrade --interactive` (never plain `upgrade`). Flip `GrainConfig.upgrade_check` default `silent → warn`; add `--check` exit-non-zero for CI. Do NOT auto-write. Full spec: audit §5.
- **Dependencies:** none (intersects P36-T07)
- **Carried from:** P36-T06

### P40-T06 — Coverage visibility + gate

- **Status:** draft
- **Description:** Add `pytest-cov` + `[tool.coverage]` and a baseline coverage gate (ratchet up). 1633 tests run today with zero coverage signal — the largest regression-escape hole for a published package.
- **Dependencies:** none
- **Carried from:** P36-T08

### P40-T07 — CI matrix + lint depth + scheduled run

- **Status:** draft
- **Description:** Add a Python 3.11/3.12/3.13 test matrix (package advertises all three, CI exercises one). Add `[tool.ruff]` (enable I/B/UP) + `ruff format --check` (current bare `ruff check` is default F/E only). Add a scheduled CI run so upstream transitive-dep regressions (textual/tree-sitter/pdfplumber) are caught without a code change.
- **Dependencies:** none
- **Carried from:** P36-T09

### P40-T08 — Workspace fleet remediation

- **Status:** draft
- **Description:** Execute audit §4's ordered, dry-run-first sequence for the **grain-owned** workspaces only: `grain init` (NOT upgrade) the live shells that hold real code — `apps/{diwa-web,gateway,sanctum}` and `products/{atlas,chronicle,key}` (`apps/eden` is a true 0-code stub — decide init vs drop); two-step `--add-missing`→`--interactive`→`init --update-agents` for `apps/apex` + `products/daemon`; `--diff`→`--interactive` for the customized-drift trio (`.`/`lore`/`grain`, where plain upgrade is a silent no-op). Excludes the familiar packages (see T12).
- **Dependencies:** P36-T12
- **Carried from:** P36-T11

### P40-T09 — Fleet taxonomy: remove non-grain workspaces + fix ledger schema

- **Status:** draft
- **Description:** `packages/{identity-kernel,vault-kit,grimoire}` are **strictly familiar runtime substrate, not grain products** — remove their stray `grain.toml` so they drop out of the grain fleet/governance entirely. Establish the taxonomy rule (grain manages `product`-type workspaces; familiar substrate is out of scope). Migrate `products/ledger/grain.toml` off the malformed legacy `[workspace]` schema to `[project]`+`[paths]` (or confirm ledger is also out of grain's scope).
- **Dependencies:** none
- **Carried from:** P36-T12

### P40-T10 — Low-priority cleanups

- **Status:** draft
- **Description:** Finish the Forge→grain rename — `ForgeError` (public, caught by name) → `GrainError` with a deprecation alias (36 refs / 9 files). Correct the stale CHANGELOG 0.4.0 entry that advertises the deleted `publish-pypi.yml`. Regenerate `Formula/grain.rb` against the real 0.5.0 sdist (currently a 0.1.0 placeholder pointing at a nonexistent tarball).
- **Dependencies:** none

---
- **Struck 2026-07-09:** the "delete `src/grain/contracts/`" bullet is reversed — spec §5.1 reserves that package and `P37-T13` populates it.
- **Carried from:** P36-T13

### P40-T11 — DRY the backlog phase-heading regex into one definition

- **Status:** draft
- **Description:** Six divergent copies of the phase-heading regex exist. Three required a numbered heading (`## N. Phase N —`) that the canonical backlog never uses, so `grain status` silently reported `Tasks: 0 total` and `docs audit` / `workflow run` mis-parsed the backlog; `metrics_service` accepted only the unnumbered form. All four were made tolerant on 2026-07-09, but the duplication remains — the exact follow-up Phase 32's notes asked for. Collapse them into one shared definition and add a guard/audit check that the backlog heading format matches what the parsers expect.
- **Files:** `src/grain/cli/status.py`, `src/grain/services/docs_audit_service.py`, `src/grain/services/workflow_run_service.py`, `src/grain/services/metrics_service.py`, `src/grain/services/workflow_service.py`, `src/grain/services/phase_archive_service.py`, `src/grain/tui/app.py`, `src/grain/services/task_advice_service.py`
- **Dependencies:** none
- **Carried from:** P36-T16

### P40-T12 — `grain status` health reads a stale cache

- **Status:** draft
- **Description:** `grain status` reported `Health: ✗ 1 error(s)` while `run_audit()` on the same tree returned `0 errors` — the cached read outlived the underlying fix. A cache that can disagree with the audit it summarizes is worse than no cache. Invalidate on working-doc mtime, or drop the cache.
- **Files:** `src/grain/cli/status.py`
- **Dependencies:** none

### P40-T13 — OIDC Trusted Publishing for grain-contracts + grain-core · TASK-0235
- **Status:** review
- **Description:** The grain-contracts 0.2.0 release 403'd at Publish because `PYPI_TOKEN_GRAIN_CONTRACTS`
  expired. Move grain-contracts + grain-core onto PyPI OIDC Trusted Publishing (no long-lived token):
  `release-python.yml` gains `id-token: write` and publishes those two with `uv publish
  --trusted-publishing always`; grain-kit/assay/pulse keep tokens via `--trusted-publishing never`.
  Operator adds a Trusted Publisher per PyPI project, then the `grain-contracts-v0.2.0` release re-runs.
- **Files:** `.github/workflows/release-python.yml`
- **Dependencies:** none
---
- **Carried from:** P36-T17
