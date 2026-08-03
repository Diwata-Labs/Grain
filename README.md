# Grain

[![PyPI](https://img.shields.io/pypi/v/grain-kit)](https://pypi.org/project/grain-kit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**A checklist your agent can't skip.**

A deterministic workflow layer for Claude Code, Codex, and similar agent CLIs: explicit task packets, scoped context, and review gates that every step must pass through before work lands.

---

## Why Grain

Grain governs agentic work of any kind — drafting and editing documents, updating spreadsheets, running multi-step research, as well as software development. The code loop is one instance of the substrate, not the whole of it.

Left to an open-ended conversation, agent-driven work tends to degrade into repeated explanations, oversized context, hidden state across sessions, and unclear review boundaries.

Grain makes the workflow explicit:

- one task packet at a time
- only load the context the task needs
- keep state in repo files, not agent memory
- require explicit review before closure

```text
Idea → Task Packet → Context → Execute → Review → Close
```

This is most useful when you are working inside an agent CLI and want the agent to follow a deterministic workflow instead of improvising.

---

## Install

Requirements: Python 3.11+, `uv` recommended

```bash
uv tool install grain-kit
```

Or with pip:

```bash
pip install grain-kit
```

Verify:

```bash
grain --version
```

---

## Quick start

### New project

```bash
mkdir my-project && cd my-project
git init
grain init
grain workflow next      # names the next legal step
grain prompt show        # surfaces the prompt to run
```

For a fresh workspace, `grain workflow next` recommends task planning and `grain prompt show` surfaces `prompts/task.plan.next.md`. Open the prompt Grain surfaces in your agent CLI and follow it exactly — Grain always names the prompt to run next, so trust `grain prompt show` over any hard-coded filename.

### Existing project

```bash
cd your-existing-project
grain onboard
grain workflow next
grain prompt show
```

Open `prompts/workflow.onboard.existing.md` in your agent CLI. That prompt scans the existing repo, drafts canonical docs, and identifies open questions. Review those docs before treating them as authoritative.

---

## How Grain organizes a repo

```text
docs/canonical/   — source-of-truth project decisions
docs/working/     — backlog, current focus, open questions
docs/runtime/     — workflow rules, adapter profiles, context-loading rules
tasks/            — one folder per task packet
prompts/          — stable prompt files for your agent CLI
```

The workflow is file-backed and inspectable. There is no hidden daemon, database, or background service.

---

## The daily loop

```bash
grain workflow next      # what is the next legal step?
grain prompt show        # surface the stable prompt entrypoint
```

Run the recommended prompt in your agent CLI, review the proposed work, then close the task when complete.

Full command set:

```bash
grain workflow next
grain workflow explain      # translate the current gate into concrete actions
grain workflow reconcile --dry-run   # repair packet/backlog drift before continuing
grain prompt show
grain review check --id TASK-0001
grain task close --id TASK-0001
grain tui                   # terminal dashboard
```

One-shot and loop modes:

```bash
grain workflow run            # execute one legal state transition, stop at gates
grain workflow loop --steps 3 # repeated state-driven execution
```

When Grain stops, use `grain workflow explain` first. Return to `grain workflow next` only after the file-backed issue is repaired.

---

## Using Grain with Claude Code and Codex

Grain is designed to be the workflow layer for any agent CLI. Paste the instruction below into your CLAUDE.md or equivalent config file:

```text
You are operating inside a repository that uses Grain as its workflow system.

Rules:
- Run `grain workflow next` before deciding what to do.
- If Grain stops or the repo state looks inconsistent, run `grain workflow explain` before improvising.
- If the explanation points to drift, run `grain workflow reconcile --dry-run` before making manual repairs.
- Run `grain prompt show` before executing the next step.
- Follow the recommended prompt exactly.
- Work on only one active task packet at a time.
- Do not bypass review or closure gates.
- Do not modify canonical docs directly.
- Do not invent workflow steps outside Grain.
```

**Codex and CLI-first usage:**

```bash
grain --format json workflow next
grain prompt show --format json
```

Use `--format json` when the calling environment wants structured state. Use text output when a human operator is driving the loop directly.

**Claude Desktop / MCP:**

```bash
grain --format json mcp manifest    # inspect available tools
grain mcp serve                     # start local stdio MCP wrapper
```

Current intent:
- Codex/tool-execution path: direct CLI
- Claude/Desktop-style path: local stdio MCP wrapper over the same Grain services
- both paths preserve the same workflow rules and packet-first boundaries

---

## Task packets

A task packet is the unit of execution. Each task lives in its own directory under `tasks/`.

```text
task.md             — description, status, acceptance criteria
context.md          — files and docs relevant to this task
plan.md             — proposed approach
deliverable_spec.md
results.md
handoff.md          — (when needed)
```

Commands:

```bash
grain task list
grain task show --id TASK-0001
grain task prepare --id TASK-0001
grain task validate --id TASK-0001
grain task create --phase 3 --task-num 4 --title "Add packet validator"
```

Small-fix example:

```bash
grain task create --phase 3 --task-num 5 --title "Fix CLI help typo"
grain workflow next
grain prompt show
grain task close --id TASK-0002 --quick --summary "Fixed the CLI help typo."
```

---

## Context control

Grain loads only the context each task needs instead of dumping the whole repo into every interaction.

```bash
grain context build --id TASK-0001
grain context show --id TASK-0001
grain context export --id TASK-0001
```

---

## Adapters

Adapters tune context selection and review focus for different types of work while keeping the workflow loop identical.

```bash
grain adapter list
grain adapter show --id code_adapter
```

Eight adapters ship, spanning code and non-code work:

- `code_adapter` — Python, Rust, backend services, CLI tooling
- `frontend_adapter` — TypeScript, JavaScript, React, Storybook, Tauri UI
- `spreadsheet_adapter` — Excel spreadsheets, CSV datasets, tabular data review
- `docs_adapter` — markdown and Word `.docx` documents, documentation-heavy repositories
- `obsidian_adapter` — Obsidian vaults, wiki-link and frontmatter-driven note systems
- `data_adapter` — data-science and ML-experimentation workflows, notebook-driven analysis, dataset and model-artifact review
- `database_adapter` — relational schema and migration planning, SQL surfaces, ORM-backed persistence
- `crawler_adapter` — crawler and scraping configs, extraction-schema and output-validation work

Declare the adapter on the task packet when the work targets that domain. Grain assembles focused context from relevant files instead of broad app code.

---

## Office documents

Grain is not code-only. It mutates real office artifacts — Word `.docx` and Excel spreadsheets — through the same packet-first, review-before-write discipline it applies to source code.

Every change is proposed first: Grain writes a candidate file plus an `office_review.json` into the active task packet, runs structure, reference, and policy validators over it, and reports residual risks. Nothing overwrites the source until you review the proposal.

```bash
grain office spreadsheet propose --source data/report.xlsx --set "Sheet1!B2=14"
grain office docx propose --source docs/brief.docx --replace "old=new"
grain office review show --task-id TASK-0001
```

`propose` writes the candidate into the packet as a `.proposed.` file for review. `export` produces a separate reviewed output file (`export-as-new-file`) rather than touching the source in place:

```bash
grain office spreadsheet export --source data/report.xlsx --set "Sheet1!B2=14"
grain office docx export --source docs/brief.docx --replace "old=new"
```

Source paths are relative to the repo root. Both commands default to the active packet (`current_task.md`); pass `--task-id TASK-####` to target another. Review the persisted `office_review.json` before closing the packet.

---

## Recipes

Recipes are the other half of the general-workflow story: a deterministic, multi-step engine for producing a document, a research brief, or any staged deliverable. A recipe is an ordered list of steps, each producing an inspectable artifact, with memory flowing between steps through declared inputs. Recipes run as their own small linear state machine **parallel to** — never inside — the task-packet loop: they never create task packets and never touch the workflow engine.

Definitions are `grain.recipe/v2` (`docs/recipes/<id>/recipe.yaml` or bundled); run state is `grain.recipe-run/v1` under `docs/recipes/runs/<run-id>/`, file-backed and resumable. Two recipes ship bundled: `explainer` (turn a topic into a short, beginner-friendly explainer) and `research-brief` (produce a sourced research brief).

A recipe's supervision mode decides who fills each step. **Operator/gated** recipes run offline and deterministic: `grain recipe run` renders the current step's prompt with its scoped inputs and pauses at `awaiting_input`; you (or an agent) write the step's output artifact, then advance. The engine never writes the artifact itself and never auto-completes — a missing output is a pause, not a failure. **Autonomous** recipes (such as `research-brief`) instead shell to your configured agent per step.

The offline operator loop, using the bundled `explainer` recipe:

```bash
grain recipe list                                     # bundled + workspace recipes
grain recipe run explainer --param topic="hash maps"  # start a run; pauses at the first step
grain recipe status --run <run-id>                    # cursor + per-step state
# write the cursor step's output artifact under docs/recipes/runs/<run-id>/, then:
grain recipe next --run <run-id>                       # advance exactly one step
grain recipe resume <run-id>                           # re-enter a paused or failed run
```

`--run <run-id>` is required whenever more than one run is open. Add `--format json` to any recipe command to drive it headlessly from an agent.

---

## Workspace health

Grain can report on the state of a workspace and surface what to do next, all from file-backed signals.

```bash
grain status        # phase, task counts, active task, workflow stage, health summary
grain doctor        # install mode, version alignment, workspace and Python checks
grain docs audit    # lint working docs AND the docs corpus for staleness signals
```

### Docs lifecycle

The docs corpus (`docs/canonical/`, `docs/working/`, `docs/archive/`) gets a full
lifecycle toolset. The guiding rule: **labels are claims, not truth** — canonical
docs can be stale, and a working doc can be more current than the canon it
overlaps. The audit never assumes canon=fresh.

```bash
grain docs search "bronze routing"   # ranked text search; spans docs_registry.external_roots
grain docs audit --doc corpus        # reference rot, subject drift, supersession queue,
                                     # verification age, orphans, duplicates, stale drafts
grain docs verify <doc>              # bump the Last-verified stamp ("reread, still true")
grain docs archive <doc>             # move to docs/archive/ + tombstone at the old path
grain docs promote <doc> --into <canon|new>   # resolve a supersession queue item
grain docs index                     # regenerate the derived index (+ Doc Health section)
```

The index and Doc Health badges are **derived, never authored**: every `grain docs`
command refreshes them incrementally before answering (extraction is cached per
file; only changed files are re-parsed — rot/drift verdicts are always computed
fresh against the current repo state). On-demand refresh is the default trigger;
recommended integrations, not installed automatically:

```bash
# git hook — keep the index fresh on every commit/merge:
echo 'grain docs index >/dev/null 2>&1 || true' >> .git/hooks/post-commit
# CI — scheduled corpus audit (non-zero exit only with --strict):
grain docs audit --format json --strict
```

Use `--no-refresh` on `docs search` / `docs audit` to skip the refresh in scripts.

`grain suggest` proposes what to pick up next from actionable signals in the workspace. Acceptance and dismissal are **subcommands**, not flags:

```bash
grain suggest              # list proposals
grain suggest accept <id>  # accept a proposal
grain suggest dismiss <id> # dismiss a proposal
```

`grain workflow guard` enforces workflow invariants — for example, that an in-progress packet exists and that implementation has not run ahead of its packet. It **exits non-zero when an invariant is violated**, so it wires directly into git hooks and CI:

```bash
grain workflow guard        # exit code 1 on any violation, 0 when clean
grain hooks install         # write Grain's pre-commit and post-checkout hooks to .git/hooks/
grain hooks status          # show whether the managed hooks are installed and current
```

---

## Review and closure

Grain keeps review explicit.

```bash
grain review check --id TASK-0001
grain review summary --id TASK-0001
grain review handoff --id TASK-0001
grain task close --id TASK-0001
```

Intelligence may propose changes. Closure is a deliberate gate.

---

## Verification (Assay integration)

Grain integrates with [Assay](https://github.com/Diwata-Domains/Assay) for visual and functional verification of tasks before closure.

```bash
grain verify submit --id TASK-0001
grain verify status --verification-id VERIFY-0001-001
grain verify ingest --verification-id VERIFY-0001-001 --payload payload.json
```

Verification rules:
- submit after the packet has `results.md` and is in `review` or `done`
- `verification_request.json` and `verification_result.json` are packet-local artifacts
- do not close a task while verification is `pending`
- if verification is `failed`, resolve the findings or explicitly waive before closure

---

## Orchestration

Generate plan proposals for larger scopes without silently mutating the repo plan.

```bash
grain orchestrate scope --scope "Add authentication system"
grain orchestrate plan --scope "Add authentication system"
grain orchestrate accept --plan OP-XXXXXXXX
```

These outputs are proposals meant to support sequencing, not bypass review.

---

## Terminal UI

`grain tui` is an operator shell over Grain's CLI and file-backed workflow.

Surfaces:
- workflow dashboard and current task status
- phase backlog and packet artifact inspection
- prompt preview and compact context summary
- blocker detail and action feedback
- execute, review, and close launchers

The TUI reads the same repo files and service outputs the CLI uses. It does not maintain hidden state or bypass review gates.

---

## What Grain is not

- a coding model
- a GUI project manager
- a hidden orchestration service
- a database-backed autonomy layer

It is a filesystem-first workflow layer for agent-assisted work of any kind.

---

## Troubleshooting

If `grain` is not found after install:

```bash
uv tool dir --bin
```

Add that directory to your `PATH`.

For a local editable install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## License

[MIT](LICENSE).

---

## Feedback

[https://github.com/Diwata-Domains/Grain/issues](https://github.com/Diwata-Domains/Grain/issues)
