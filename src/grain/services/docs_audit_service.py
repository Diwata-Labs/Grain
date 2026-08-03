# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Docs audit service — read-only workspace health checks across 6 document types."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

_CURRENT_TASK_PATH = "docs/working/current_task.md"
_BACKLOG_PATH = "docs/working/backlog.md"
_CURRENT_FOCUS_PATH = "docs/working/current_focus.md"
_PROJECT_STATE_PATH = "docs/working/project_state.md"
_OQ_PATH = "docs/working/open_questions.md"
_TOOLING_NOTES_PATH = "docs/working/tooling_notes.md"
_PROPOSALS_PATH = "docs/working/change_proposals.md"
_MANIFEST_PATH = "docs/runtime/docs_manifest.yaml"

_TASK_REF_RE = re.compile(r"P\d+-T\d+")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_ACTIVE_RE = re.compile(r"Phase\s+(\d+)\b[^\n]*?\bactive\b", re.IGNORECASE)
_CLOSED_LINE_RE = re.compile(r"Phase\s+(\d+)\b[^\n]*?\b(?:CLOSED|closed)\b", re.IGNORECASE)
# A Closed-Phase Ledger table row: "| 31 | Title | date | tasks | milestone |"
# whose first cell is a phase number or a range like "1–5" / "1-5". These rows
# carry NEITHER the word "Phase" NOR a closed-status word, so they are invisible
# to _CLOSED_LINE_RE; the ledger section parser below recovers them explicitly.
_LEDGER_HEADING_RE = re.compile(r"^#{1,6}\s.*\bClosed-Phase Ledger\b", re.IGNORECASE)
_LEDGER_ROW_RE = re.compile(r"^\|\s*(\d+)\s*(?:[–\-]\s*(\d+)\s*)?\|")

# Cross-document phase declarations. These match how the working docs name the
# active/current phase: current_focus.md uses a "## Current Phase" heading; the
# bullet-style "**Phase:** N" / "**Active phase:** Phase N" forms appear in
# project_state.md; a bare "Phase: N" / "Phase N" line covers current_task.md.
_DECLARED_PHASE_RES = (
    re.compile(r"\*\*Active\s+phase:\*\*\s*(?:Phase\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"\*\*Current\s+phase:\*\*\s*(?:Phase\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"\*\*Phase:\*\*\s*(?:Phase\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"^Active\s+phase:\s*(?:Phase\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"^Phase:\s*(?:Phase\s+)?(\d+)", re.IGNORECASE),
)

# Archive-claim mining: "archived to `tasks/archive/phase-7/`" and bare
# "tasks/archive/phase-7" references that assert an on-disk task archive exists.
_ARCHIVE_CLAIM_RE = re.compile(r"tasks/archive/phase-(\d+)\b")

# Task-ID counter declarations in runtime/registered docs, e.g.
# "highest task ID is TASK-0031" or "next task ID: TASK-0032". The leading
# keyword keeps us from matching ordinary task references in prose.
_TASK_COUNTER_RE = re.compile(
    r"(?:highest|next|last|latest|max(?:imum)?)\s+task\s*id"
    r"[^\n]*?\bTASK-(\d+)\b",
    re.IGNORECASE,
)
_TASK_ID_NUM_RE = re.compile(r"TASK-(\d+)")


# ── Domain objects ─────────────────────────────────────────────────────────────

@dataclass
class AuditFinding:
    doc: str
    check_id: str
    severity: str   # "error" | "warning" | "pass"
    message: str
    remediation: str = ""


@dataclass
class AuditResult:
    run_at: str
    summary: dict
    overall: str    # "ok" | "warning" | "error"
    findings: list[AuditFinding] = field(default_factory=list)


@dataclass
class AuditConfig:
    current_task_idle_days: int = 14
    current_focus_stale_days: int = 30
    oq_blocking_max: int = 3
    oq_stale_open_days: int = 60
    tooling_notes_high_severity_aging_days: int = 14
    tooling_notes_overdue_triage_max: int = 5
    proposal_aging_days: int = 30
    # corpus staleness signals (labels are claims, not truth)
    canon_unverified_days: int = 90
    subject_drift_commits: int = 10
    draft_archive_days: int = 120


# ── Check group filters ────────────────────────────────────────────────────────

_DOC_FILTER_MAP = {
    "current_task": _CURRENT_TASK_PATH,
    "backlog": _BACKLOG_PATH,
    "current_focus": _CURRENT_FOCUS_PATH,
    "open_questions": _OQ_PATH,
    "tooling_notes": _TOOLING_NOTES_PATH,
    "change_proposals": _PROPOSALS_PATH,
    "structural": "structural",
    "cross_doc": "cross_doc",
}

# Corpus-level staleness signals. Each is separately selectable via
# ``--doc <signal>`` and all run under ``--doc corpus`` (and by default).
_CORPUS_SIGNALS = frozenset({
    "reference_rot",
    "subject_drift",
    "supersession",
    "verification_age",
    "orphans",
    "duplicate_topics",
    "stale_drafts",
    "manifest_reconciliation",
})

# Structural workflow docs — part of the grain workspace machinery, never
# lifecycle candidates (they are edited in place forever, not promoted/archived).
_WORKFLOW_DOC_NAMES = frozenset({
    "current_task.md", "backlog.md", "current_focus.md", "open_questions.md",
    "tooling_notes.md", "change_proposals.md", "workflow_metrics.md",
    "project_state.md", "implementation_plan.md", "roadmap.md",
})


# ── Public API ─────────────────────────────────────────────────────────────────

def run_audit(
    root: Path,
    doc_filter: str | None = None,
    severity_filter: str | None = None,
    progress=None,
) -> AuditResult:
    """Run all checks (or filtered subset) and return structured results.

    ``progress`` is an optional ``Callable[[str], None]`` invoked with short
    status lines during potentially slow corpus phases (git-backed signals over
    large corpora), so callers can avoid silent hangs.
    """
    config = _load_config(root)
    all_findings: list[AuditFinding] = []

    groups = _resolve_groups(doc_filter)

    if "current_task" in groups:
        all_findings.extend(_check_current_task(root, config))
    if "backlog" in groups:
        all_findings.extend(_check_backlog(root))
    if "current_focus" in groups:
        all_findings.extend(_check_current_focus(root, config))
    if "open_questions" in groups:
        all_findings.extend(_check_open_questions(root, config))
    if "tooling_notes" in groups:
        all_findings.extend(_check_tooling_notes(root, config))
    if "change_proposals" in groups:
        all_findings.extend(_check_change_proposals(root, config))
    if "structural" in groups:
        all_findings.extend(_check_structural(root))
    if "cross_doc" in groups:
        all_findings.extend(_check_cross_doc(root))

    requested_signals = groups & _CORPUS_SIGNALS
    if requested_signals:
        all_findings.extend(
            _check_corpus(root, config, requested_signals, progress=progress)
        )

    if severity_filter == "high":
        visible = [f for f in all_findings if f.severity == "error"]
    elif severity_filter == "medium":
        visible = [f for f in all_findings if f.severity in ("error", "warning")]
    else:
        visible = all_findings

    errors = [f for f in visible if f.severity == "error"]
    warnings = [f for f in visible if f.severity == "warning"]
    passes = [f for f in all_findings if f.severity == "pass"]

    if errors:
        overall = "error"
    elif warnings:
        overall = "warning"
    else:
        overall = "ok"

    return AuditResult(
        run_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        summary={"pass": len(passes), "warning": len(warnings), "error": len(errors)},
        overall=overall,
        findings=visible,
    )


def save_audit_cache(root: Path, result: AuditResult) -> None:
    """Write result to .grain/last_docs_audit.json."""
    grain_dir = root / ".grain"
    grain_dir.mkdir(exist_ok=True)
    cache_path = grain_dir / "last_docs_audit.json"
    data = {
        "run_at": result.run_at,
        "summary": result.summary,
        "overall": result.overall,
        "findings": [
            {
                "doc": f.doc,
                "check_id": f.check_id,
                "severity": f.severity,
                "message": f.message,
                "remediation": f.remediation,
            }
            for f in result.findings
            if f.severity != "pass"
        ],
    }
    cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def apply_fixes(root: Path, result: AuditResult, *, confirm: bool = True) -> list[str]:
    """Apply safe auto-fixes. Returns list of applied fix descriptions."""
    applied: list[str] = []
    for finding in result.findings:
        if finding.check_id == "current_task_stale_pointer":
            if confirm:
                import click
                if not click.confirm(f"  Clear stale pointer in {_CURRENT_TASK_PATH}?", default=False):
                    continue
            _clear_current_task(root)
            applied.append("cleared stale pointer in current_task.md")
    return applied


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config(root: Path) -> AuditConfig:
    manifest_path = root / _MANIFEST_PATH
    if not manifest_path.exists():
        return AuditConfig()
    try:
        import yaml  # type: ignore
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        thresholds = manifest.get("audit_thresholds", {}) if manifest else {}
        return AuditConfig(
            current_task_idle_days=thresholds.get("current_task_idle_days", 14),
            current_focus_stale_days=thresholds.get("current_focus_stale_days", 30),
            oq_blocking_max=thresholds.get("oq_blocking_max", 3),
            oq_stale_open_days=thresholds.get("oq_stale_open_days", 60),
            tooling_notes_high_severity_aging_days=thresholds.get(
                "tooling_notes_high_severity_aging_days", 14
            ),
            tooling_notes_overdue_triage_max=thresholds.get("tooling_notes_overdue_triage_max", 5),
            proposal_aging_days=thresholds.get("proposal_aging_days", 30),
            canon_unverified_days=thresholds.get("canon_unverified_days", 90),
            subject_drift_commits=thresholds.get("subject_drift_commits", 10),
            draft_archive_days=thresholds.get("draft_archive_days", 120),
        )
    except Exception:
        return AuditConfig()


def _resolve_groups(doc_filter: str | None) -> set[str]:
    all_groups = {
        "current_task", "backlog", "current_focus",
        "open_questions", "tooling_notes", "change_proposals", "structural",
        "cross_doc",
    } | set(_CORPUS_SIGNALS)
    if not doc_filter:
        return all_groups
    key = doc_filter.replace(".md", "")
    if key == "corpus":
        return set(_CORPUS_SIGNALS)
    return {key} if key in all_groups else all_groups


# ── current_task.md checks ────────────────────────────────────────────────────

def _check_current_task(root: Path, config: AuditConfig) -> list[AuditFinding]:
    doc = _CURRENT_TASK_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="current_task_stale_pointer",
                             severity="error", message=f"{doc} is missing",
                             remediation="grain init")]

    findings: list[AuditFinding] = []
    ct = _parse_current_task(path)
    task_id = ct.get("task_id", "none")

    # current_task_stale_pointer
    if task_id and task_id != "none":
        task_path = ct.get("task_path", "")
        packet_dir = _resolve_packet(root, task_id, task_path)
        if packet_dir and (packet_dir / "task.md").exists():
            from grain.domain.packets import parse_task_metadata
            meta = parse_task_metadata(packet_dir / "task.md")
            if meta.get("status") == "done":
                findings.append(AuditFinding(
                    doc=doc, check_id="current_task_stale_pointer", severity="error",
                    message=f"current_task.md points to completed packet: {task_id}",
                    remediation="grain docs audit --fix  (or set 'Task ID: none' manually)",
                ))
            else:
                findings.append(AuditFinding(
                    doc=doc, check_id="current_task_stale_pointer", severity="pass",
                    message=f"no stale pointer ({task_id} is {meta.get('status', 'unknown')})",
                ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_task_stale_pointer", severity="pass",
                message="no stale pointer",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="current_task_stale_pointer", severity="pass",
            message="no active task pointer",
        ))

    # current_task_missing_packet
    if task_id and task_id != "none":
        task_path = ct.get("task_path", "")
        packet_dir = _resolve_packet(root, task_id, task_path)
        if packet_dir is None:
            findings.append(AuditFinding(
                doc=doc, check_id="current_task_missing_packet", severity="error",
                message=f"current_task.md references {task_id} but no packet directory found",
                remediation=f"grain task create --id {task_id}",
            ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_task_missing_packet", severity="pass",
                message=f"packet {task_id} exists",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="current_task_missing_packet", severity="pass",
            message="no active task pointer",
        ))

    # current_task_idle
    if config.current_task_idle_days > 0:
        if not task_id or task_id == "none":
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            age = datetime.now(tz=timezone.utc) - mtime
            if age > timedelta(days=config.current_task_idle_days):
                findings.append(AuditFinding(
                    doc=doc, check_id="current_task_idle", severity="warning",
                    message=f"no active task for {age.days} days (threshold: {config.current_task_idle_days})",
                    remediation="grain workflow next",
                ))
            else:
                findings.append(AuditFinding(
                    doc=doc, check_id="current_task_idle", severity="pass",
                    message=f"workspace active ({age.days} days since last change)",
                ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_task_idle", severity="pass",
                message="task is active",
            ))
    return findings


# ── backlog.md checks ─────────────────────────────────────────────────────────

def _check_backlog(root: Path) -> list[AuditFinding]:
    doc = _BACKLOG_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="backlog_inprogress_no_packet",
                             severity="error", message=f"{doc} is missing",
                             remediation="grain upgrade --add-missing")]

    findings: list[AuditFinding] = []
    tasks_root = root / "tasks"
    phases = _parse_backlog_phases(path.read_text(encoding="utf-8"))

    inprogress_no_packet: list[str] = []
    done_no_results: list[str] = []

    for phase in phases:
        for task in phase["tasks"]:
            task_ref = task["ref"]
            task_id = task.get("task_id", "")
            status = task.get("status", "")

            if status == "in_progress":
                packet_ok = False
                if task_id:
                    packet_dir = _find_packet_by_id(tasks_root, task_id)
                    if packet_dir and (packet_dir / "task.md").exists():
                        from grain.domain.packets import parse_task_metadata
                        meta = parse_task_metadata(packet_dir / "task.md")
                        if meta.get("status") == "in_progress":
                            packet_ok = True
                if not packet_ok:
                    inprogress_no_packet.append(task_ref)

            elif status == "done":
                if task_id:
                    packet_dir = _find_packet_by_id(tasks_root, task_id)
                    if packet_dir and not (packet_dir / "results.md").exists():
                        done_no_results.append(task_ref)

    if inprogress_no_packet:
        for ref in inprogress_no_packet:
            findings.append(AuditFinding(
                doc=doc, check_id="backlog_inprogress_no_packet", severity="error",
                message=f"{ref} is in_progress in backlog but has no open packet",
                remediation=f"grain task create  (or check tasks/ for {ref})",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="backlog_inprogress_no_packet", severity="pass",
            message="all in_progress tasks have open packets",
        ))

    if done_no_results:
        for ref in done_no_results:
            findings.append(AuditFinding(
                doc=doc, check_id="backlog_done_no_results", severity="warning",
                message=f"{ref} is done but has no results.md in its packet",
                remediation=f"add results.md to the {ref} packet",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="backlog_done_no_results", severity="pass",
            message="all done tasks with packets have results.md",
        ))

    # phase drift: phase in_progress but all tasks done
    phase_drift: list[str] = []
    for phase in phases:
        if not phase["tasks"]:
            continue
        phase_status = phase.get("status", "")
        if phase_status == "in_progress":
            all_done = all(t.get("status") == "done" for t in phase["tasks"])
            if all_done:
                phase_drift.append(phase["name"])

    if phase_drift:
        for name in phase_drift:
            findings.append(AuditFinding(
                doc=doc, check_id="backlog_phase_status_drift", severity="warning",
                message=f"Phase {name!r} is in_progress but all tasks are done",
                remediation="grain phase close (when ready)",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="backlog_phase_status_drift", severity="pass",
            message="no in_progress phases with all tasks done",
        ))

    # closed phase with open tasks
    closed_with_open: list[str] = []
    for phase in phases:
        if phase.get("closed"):
            non_done = [t for t in phase["tasks"] if t.get("status") not in ("done", "")]
            if non_done:
                closed_with_open.append(phase["name"])

    if closed_with_open:
        for name in closed_with_open:
            findings.append(AuditFinding(
                doc=doc, check_id="backlog_phase_closed_with_open_tasks", severity="error",
                message=f"Phase {name!r} is marked CLOSED but has non-done tasks",
                remediation="review and resolve open tasks before closing phase",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="backlog_phase_closed_with_open_tasks", severity="pass",
            message="no closed phases have open tasks",
        ))

    return findings


# ── current_focus.md checks ───────────────────────────────────────────────────

def _check_current_focus(root: Path, config: AuditConfig) -> list[AuditFinding]:
    doc = _CURRENT_FOCUS_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="current_focus_phase_mismatch",
                             severity="error", message=f"{doc} is missing",
                             remediation="grain upgrade --add-missing")]

    findings: list[AuditFinding] = []
    text = path.read_text(encoding="utf-8")

    # current_focus_phase_mismatch
    phase_line = _extract_current_phase(text)
    if phase_line:
        backlog_path = root / _BACKLOG_PATH
        if backlog_path.exists():
            backlog_text = backlog_path.read_text(encoding="utf-8")
            # Look for the phase number in backlog phase headings
            phase_num_match = re.search(r"Phase\s+(\d+)", phase_line)
            if phase_num_match:
                phase_num = phase_num_match.group(1)
                backlog_phase_re = re.compile(rf"##\s+(?:\d+\.\s+)?Phase\s+{re.escape(phase_num)}\b")
                if backlog_phase_re.search(backlog_text):
                    findings.append(AuditFinding(
                        doc=doc, check_id="current_focus_phase_mismatch", severity="pass",
                        message=f"phase {phase_num} found in backlog",
                    ))
                else:
                    findings.append(AuditFinding(
                        doc=doc, check_id="current_focus_phase_mismatch", severity="warning",
                        message=f"current_focus.md references Phase {phase_num} but it's not in backlog.md",
                        remediation="update current_focus.md or add the phase to backlog.md",
                    ))
            else:
                findings.append(AuditFinding(
                    doc=doc, check_id="current_focus_phase_mismatch", severity="pass",
                    message="current phase format not standard — skipped",
                ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_focus_phase_mismatch", severity="pass",
                message="backlog.md absent — skipped",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="current_focus_phase_mismatch", severity="pass",
            message="no Current Phase line found — skipped",
        ))

    # current_focus_stale
    if config.current_focus_stale_days > 0:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(tz=timezone.utc) - mtime
        if age > timedelta(days=config.current_focus_stale_days):
            findings.append(AuditFinding(
                doc=doc, check_id="current_focus_stale", severity="warning",
                message=f"current_focus.md last modified {age.days} days ago (threshold: {config.current_focus_stale_days})",
                remediation="update current_focus.md with the current phase state",
            ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_focus_stale", severity="pass",
                message=f"recently updated ({age.days} days ago)",
            ))

    # current_focus_priorities_done
    priority_refs = _extract_priority_task_refs(text)
    if priority_refs:
        backlog_path = root / _BACKLOG_PATH
        if backlog_path.exists():
            backlog_text = backlog_path.read_text(encoding="utf-8")
            statuses = {ref: _get_task_status_in_backlog(backlog_text, ref) for ref in priority_refs}
            all_done = all(s == "done" for s in statuses.values() if s)
            known_refs = [r for r, s in statuses.items() if s]
            if known_refs and all_done:
                findings.append(AuditFinding(
                    doc=doc, check_id="current_focus_priorities_done", severity="warning",
                    message=f"all referenced priority tasks are done: {', '.join(priority_refs)}",
                    remediation="update Immediate Priorities in current_focus.md",
                ))
            else:
                findings.append(AuditFinding(
                    doc=doc, check_id="current_focus_priorities_done", severity="pass",
                    message="at least one priority task is not yet done",
                ))
        else:
            findings.append(AuditFinding(
                doc=doc, check_id="current_focus_priorities_done", severity="pass",
                message="backlog.md absent — skipped",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="current_focus_priorities_done", severity="pass",
            message="no task references in Immediate Priorities",
        ))

    # phase_status_consistency
    findings.extend(_check_phase_status_consistency(text))

    return findings


def _check_phase_status_consistency(text: str) -> list[AuditFinding]:
    """Flag a phase that current_focus.md describes as BOTH active and closed,
    or a 'Current Phase' value that contradicts the closed-phase ledger."""
    doc = _CURRENT_FOCUS_PATH
    findings: list[AuditFinding] = []

    # 1. Collect every phase number marked closed anywhere in the file
    #    (prose/log lines via "Phase N ... CLOSED/closed") AND, authoritatively,
    #    the Closed-Phase Ledger table rows — which carry no "Phase"/"closed"
    #    keywords and so are invisible to _CLOSED_LINE_RE.
    closed_phases: set[str] = set()
    for line in text.splitlines():
        m = _CLOSED_LINE_RE.search(line)
        if m:
            closed_phases.add(m.group(1))
    closed_phases |= _ledger_closed_phases(text)

    # 2. Collect every phase number explicitly marked active.
    active_phases: set[str] = set()
    for line in text.splitlines():
        m = _ACTIVE_RE.search(line)
        if m:
            active_phases.add(m.group(1))

    # 3. The declared "Current Phase" pointer is treated as active too.
    current_phase_line = _extract_current_phase(text)
    current_phase_num = ""
    if current_phase_line:
        cm = re.search(r"Phase\s+(\d+)", current_phase_line)
        if cm:
            current_phase_num = cm.group(1)
            active_phases.add(current_phase_num)

    # Contradiction A: same phase number is described as both active and closed.
    contradictions = sorted(active_phases & closed_phases, key=int)
    if contradictions:
        for num in contradictions:
            findings.append(AuditFinding(
                doc=doc, check_id="phase_status_consistency", severity="error",
                message=(
                    f"Phase {num} is described as both active and closed in "
                    f"current_focus.md"
                ),
                remediation=(
                    "remove the stale status; a phase is either the active "
                    "Current Phase or a closed-ledger row, never both"
                ),
            ))
        return findings

    # Contradiction B: the Current Phase pointer is itself in the closed ledger.
    if current_phase_num and current_phase_num in closed_phases:
        findings.append(AuditFinding(
            doc=doc, check_id="phase_status_consistency", severity="error",
            message=(
                f"Current Phase is Phase {current_phase_num} but Phase "
                f"{current_phase_num} appears as closed in the ledger"
            ),
            remediation="advance Current Phase to the next open phase",
        ))
        return findings

    findings.append(AuditFinding(
        doc=doc, check_id="phase_status_consistency", severity="pass",
        message="no phase is marked both active and closed",
    ))
    return findings


def _ledger_closed_phases(text: str) -> set[str]:
    """Return phase numbers listed as rows of the Closed-Phase Ledger table.

    The ledger is the authoritative closed-phase list. Its rows look like
    ``| 31 | Title | date | tasks | milestone |`` (or a range ``| 1–5 | ... |``)
    and contain neither the word "Phase" nor a closed-status word, so they are
    parsed structurally here rather than by keyword. Range rows expand to every
    phase number in the inclusive span. Parsing is scoped to the ledger section
    (from its heading until the next heading) so unrelated tables are ignored.
    """
    closed: set[str] = set()
    in_ledger = False
    for line in text.splitlines():
        if _LEDGER_HEADING_RE.match(line):
            in_ledger = True
            continue
        if in_ledger and line.startswith("#"):
            break  # left the ledger section
        if not in_ledger:
            continue
        m = _LEDGER_ROW_RE.match(line.strip())
        if not m:
            continue
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        if end < start:
            start, end = end, start
        for n in range(start, end + 1):
            closed.add(str(n))
    return closed


# ── open_questions.md checks ──────────────────────────────────────────────────

def _check_open_questions(root: Path, config: AuditConfig) -> list[AuditFinding]:
    doc = _OQ_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="oq_blocking_accumulation",
                             severity="pass", message=f"{doc} absent — skipped")]

    findings: list[AuditFinding] = []
    text = path.read_text(encoding="utf-8")

    # Parse status lines in open questions section (before "## Resolved")
    resolved_pos = text.find("## Resolved")
    open_section = text[:resolved_pos] if resolved_pos != -1 else text

    blocking_count = 0
    stale_open: list[tuple[str, int]] = []
    now = datetime.now(tz=timezone.utc)

    # Track current entry context (title + date + status)
    current_title = ""
    current_date: str | None = None
    current_status = ""

    _OQ_HEADING_RE = re.compile(r"^###\s+(.+)$")
    _STATUS_RE = re.compile(r"-\s+\*\*Status:\*\*\s*(\S+)")
    _RAISED_RE = re.compile(r"-\s+\*\*Raised:\*\*\s*(\d{4}-\d{2}-\d{2})")

    def flush_entry():
        nonlocal blocking_count, current_title, current_date, current_status
        if current_status in ("blocking", "decision_needed"):
            blocking_count += 1
        if current_status == "open" and current_date:
            try:
                raised = datetime.strptime(current_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (now - raised).days
                if age > config.oq_stale_open_days:
                    stale_open.append((current_title or "unknown", age))
            except ValueError:
                pass
        current_title = ""
        current_date = None
        current_status = ""

    for line in open_section.splitlines():
        h = _OQ_HEADING_RE.match(line)
        if h:
            flush_entry()
            current_title = h.group(1).strip()
            continue
        s = _STATUS_RE.match(line)
        if s:
            current_status = s.group(1).lower().rstrip(".,")
            continue
        r = _RAISED_RE.match(line)
        if r:
            current_date = r.group(1)

    flush_entry()

    # oq_blocking_accumulation
    if config.oq_blocking_max > 0 and blocking_count > config.oq_blocking_max:
        findings.append(AuditFinding(
            doc=doc, check_id="oq_blocking_accumulation", severity="warning",
            message=f"{blocking_count} blocking/decision_needed questions (threshold: {config.oq_blocking_max})",
            remediation="resolve or defer blocking questions before they accumulate",
        ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="oq_blocking_accumulation", severity="pass",
            message=f"{blocking_count} blocking question(s) (within threshold)",
        ))

    # oq_stale_open
    if stale_open:
        for title, age in stale_open:
            findings.append(AuditFinding(
                doc=doc, check_id="oq_stale_open", severity="warning",
                message=f"'{title}' has been open for {age} days (threshold: {config.oq_stale_open_days})",
                remediation="resolve, defer, or update the raised date if still active",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="oq_stale_open", severity="pass",
            message="no stale open questions",
        ))

    return findings


# ── tooling_notes.md checks ───────────────────────────────────────────────────

def _check_tooling_notes(root: Path, config: AuditConfig) -> list[AuditFinding]:
    doc = _TOOLING_NOTES_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="tooling_notes_overdue_triage",
                             severity="pass", message=f"{doc} absent — skipped")]

    findings: list[AuditFinding] = []
    now = datetime.now(tz=timezone.utc)

    # Parse via the shared notes reader so both legacy six-column (Date-first)
    # rows and the canonical seven-column (ID-first) rows that `grain notes add`
    # now writes are understood. A schema change in the table must never silently
    # blind the aging/overdue checks.
    from grain.services.notes_service import _read_notes

    notes = _read_notes(path)
    open_entries: list[tuple[str, str]] = [  # (date, severity)
        (n.created_at, n.severity.lower()) for n in notes if n.status == "open"
    ]

    # tooling_notes_high_severity_aging
    aging_high: list[int] = []
    if config.tooling_notes_high_severity_aging_days > 0:
        for date_str, severity in open_entries:
            if severity == "high":
                try:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    age = (now - entry_date).days
                    if age > config.tooling_notes_high_severity_aging_days:
                        aging_high.append(age)
                except ValueError:
                    pass

    if aging_high:
        findings.append(AuditFinding(
            doc=doc, check_id="tooling_notes_high_severity_aging", severity="warning",
            message=f"{len(aging_high)} high-severity entry(ies) open >{config.tooling_notes_high_severity_aging_days} days",
            remediation="triage or escalate high-severity tooling notes",
        ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="tooling_notes_high_severity_aging", severity="pass",
            message="no aging high-severity entries",
        ))

    # tooling_notes_overdue_triage
    open_count = len(open_entries)
    if config.tooling_notes_overdue_triage_max > 0 and open_count > config.tooling_notes_overdue_triage_max:
        findings.append(AuditFinding(
            doc=doc, check_id="tooling_notes_overdue_triage", severity="warning",
            message=f"{open_count} open entries (threshold: {config.tooling_notes_overdue_triage_max})",
            remediation="review and triage tooling_notes.md",
        ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="tooling_notes_overdue_triage", severity="pass",
            message=f"{open_count} open entries (within threshold)",
        ))

    # tooling_notes_open_friction — open bug/friction notes are low-severity
    # findings so they stay visible until resolved via `grain notes resolve`.
    open_actionable = _open_actionable_notes(path)
    if open_actionable:
        for note_id, note_type, body in open_actionable:
            preview = body if len(body) <= 80 else body[:77] + "…"
            findings.append(AuditFinding(
                doc=doc, check_id="tooling_notes_open_friction", severity="warning",
                message=f"open {note_type} note #{note_id}: {preview}",
                remediation=f"grain notes resolve {note_id}",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="tooling_notes_open_friction", severity="pass",
            message="no open bug/friction notes",
        ))

    return findings


def _open_actionable_notes(path: Path) -> list[tuple[int, str, str]]:
    """Return (id, type, body) for open bug/friction notes in tooling_notes.md.

    IDs come from the same reader the notes service uses, so the remediation it
    emits (``grain notes resolve <id>``) always targets an ID that show/resolve
    actually accept — including synthesized IDs for legacy rows.
    """
    from grain.domain.notes import ACTIONABLE_TYPES, OPEN_STATUSES
    from grain.services.notes_service import _read_notes

    result: list[tuple[int, str, str]] = []
    for note in _read_notes(path):
        if note.type in ACTIONABLE_TYPES and note.status in OPEN_STATUSES:
            result.append((note.id, note.type, note.body))
    return result


# ── change_proposals.md checks ────────────────────────────────────────────────

def _check_change_proposals(root: Path, config: AuditConfig) -> list[AuditFinding]:
    doc = _PROPOSALS_PATH
    path = root / doc
    if not path.exists():
        return [AuditFinding(doc=doc, check_id="proposal_aging",
                             severity="pass", message=f"{doc} absent — skipped")]

    findings: list[AuditFinding] = []
    text = path.read_text(encoding="utf-8")
    now = datetime.now(tz=timezone.utc)

    # Look for proposed-status entries with a Raised date
    aging_proposals: list[tuple[str, int]] = []
    current_title = ""
    current_date: str | None = None
    current_status = ""

    _CP_HEADING_RE = re.compile(r"^###\s+(.+)$")
    _STATUS_RE = re.compile(r"-\s+\*\*Status:\*\*\s*(\S+)")
    _RAISED_RE = re.compile(r"-\s+\*\*Raised:\*\*\s*(\d{4}-\d{2}-\d{2})")

    def flush():
        nonlocal current_title, current_date, current_status
        if current_status == "proposed" and current_date and config.proposal_aging_days > 0:
            try:
                raised = datetime.strptime(current_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (now - raised).days
                if age > config.proposal_aging_days:
                    aging_proposals.append((current_title, age))
            except ValueError:
                pass
        current_title = ""
        current_date = None
        current_status = ""

    for line in text.splitlines():
        h = _CP_HEADING_RE.match(line)
        if h:
            flush()
            current_title = h.group(1).strip()
            continue
        s = _STATUS_RE.match(line)
        if s:
            current_status = s.group(1).lower().rstrip(".,")
            continue
        r = _RAISED_RE.match(line)
        if r:
            current_date = r.group(1)

    flush()

    if aging_proposals:
        for title, age in aging_proposals:
            findings.append(AuditFinding(
                doc=doc, check_id="proposal_aging", severity="warning",
                message=f"'{title}' has been proposed for {age} days (threshold: {config.proposal_aging_days})",
                remediation="approve, reject, or defer the proposal",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="proposal_aging", severity="pass",
            message="no aging proposals",
        ))

    return findings


# ── Structural checks ─────────────────────────────────────────────────────────

def _check_structural(root: Path) -> list[AuditFinding]:
    doc = "structural"
    manifest_path = root / _MANIFEST_PATH
    if not manifest_path.exists():
        return [AuditFinding(doc=doc, check_id="registered_doc_missing",
                             severity="error",
                             message=f"{_MANIFEST_PATH} is missing — cannot run structural checks",
                             remediation="grain init")]

    try:
        import yaml
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return [AuditFinding(doc=doc, check_id="registered_doc_missing",
                             severity="error",
                             message=f"{_MANIFEST_PATH} could not be parsed",
                             remediation="repair docs_manifest.yaml")]

    findings: list[AuditFinding] = []
    all_entries = _collect_manifest_doc_entries(manifest)

    missing: list[str] = []
    empty: list[str] = []

    for entry in all_entries:
        path_str = entry.get("path", "")
        if not path_str or path_str.endswith("/"):
            continue  # skip directory entries
        target = root / path_str
        if not target.exists():
            missing.append(path_str)
        else:
            content = target.read_text(encoding="utf-8")
            if _is_template_only(content):
                empty.append(path_str)

    if missing:
        for path_str in missing:
            findings.append(AuditFinding(
                doc=doc, check_id="registered_doc_missing", severity="error",
                message=f"registered doc missing: {path_str}",
                remediation="grain upgrade --add-missing",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="registered_doc_missing", severity="pass",
            message=f"all {len(all_entries)} registered docs present",
        ))

    if empty:
        for path_str in empty:
            findings.append(AuditFinding(
                doc=doc, check_id="registered_doc_empty", severity="warning",
                message=f"{path_str} has no content beyond template headings",
                remediation=f"add content to {path_str}",
            ))
    else:
        findings.append(AuditFinding(
            doc=doc, check_id="registered_doc_empty", severity="pass",
            message="all registered docs have substantive content",
        ))

    # required_section_missing — only fires if manifest declares required_sections
    section_findings = _check_required_sections(root, all_entries)
    findings.extend(section_findings)

    return findings


def _check_required_sections(root: Path, entries: list[dict]) -> list[AuditFinding]:
    """Check required sections if declared in manifest entries."""
    findings: list[AuditFinding] = []
    sections_checked = 0
    sections_missing = 0
    for entry in entries:
        required_sections = entry.get("required_sections", [])
        if not required_sections:
            continue
        path_str = entry.get("path", "")
        target = root / path_str
        if not target.exists():
            continue
        content = target.read_text(encoding="utf-8")
        headings = {line.lstrip("#").strip() for line in content.splitlines() if line.startswith("#")}
        for section in required_sections:
            sections_checked += 1
            if section not in headings:
                sections_missing += 1
                findings.append(AuditFinding(
                    doc="structural", check_id="required_section_missing", severity="warning",
                    message=f"{path_str} missing required section: '{section}'",
                    remediation=f"add '## {section}' to {path_str}",
                ))

    if sections_checked == 0:
        findings.append(AuditFinding(
            doc="structural", check_id="required_section_missing", severity="pass",
            message="no required sections declared in manifest",
        ))
    elif sections_missing == 0:
        findings.append(AuditFinding(
            doc="structural", check_id="required_section_missing", severity="pass",
            message=f"all {sections_checked} required section(s) present",
        ))
    return findings


# ── Cross-document / structural drift checks ──────────────────────────────────

def _check_cross_doc(root: Path) -> list[AuditFinding]:
    """Cross-document drift checks: catch the failure modes that single-doc
    checks miss because the contradiction only exists *between* documents.

    1. cross_doc_phase_agreement — multiple working docs naming different active
       phase numbers.
    2. archive_claim_missing — a doc claims a phase was archived to a
       ``tasks/archive/phase-N/`` directory that does not exist on disk.
    3. task_id_counter_drift — a registered doc declares a "highest/next task ID"
       that no longer matches the real maximum TASK-#### on disk.
    """
    findings: list[AuditFinding] = []
    findings.extend(_check_cross_doc_phase_agreement(root))
    findings.extend(_check_archive_claim_missing(root))
    findings.extend(_check_task_id_counter_drift(root))
    return findings


def _check_cross_doc_phase_agreement(root: Path) -> list[AuditFinding]:
    """Flag when two working docs declare DIFFERENT active phase numbers.

    Collects the declared active/current phase number from current_focus.md,
    current_task.md, and project_state.md (each optional). Degrades to pass when
    fewer than two docs declare a phase.
    """
    doc = "cross_doc"
    sources = (
        (_CURRENT_FOCUS_PATH, "current_focus.md"),
        (_CURRENT_TASK_PATH, "current_task.md"),
        (_PROJECT_STATE_PATH, "project_state.md"),
    )

    declared: list[tuple[str, str]] = []  # (doc_label, phase_number)
    for rel_path, label in sources:
        path = root / rel_path
        if not path.exists():
            continue
        phase = _declared_phase_number(path.read_text(encoding="utf-8"))
        if phase:
            declared.append((label, phase))

    if len(declared) < 2:
        return [AuditFinding(
            doc=doc, check_id="cross_doc_phase_agreement", severity="pass",
            message="fewer than two docs declare an active phase — skipped",
        )]

    distinct = {num for _, num in declared}
    if len(distinct) > 1:
        detail = ", ".join(f"{label}=Phase {num}" for label, num in declared)
        return [AuditFinding(
            doc=doc, check_id="cross_doc_phase_agreement", severity="error",
            message=f"working docs disagree on the active phase: {detail}",
            remediation=(
                "reconcile the active phase across current_focus.md, "
                "current_task.md, and project_state.md so they name one phase"
            ),
        )]

    agreed = next(iter(distinct))
    return [AuditFinding(
        doc=doc, check_id="cross_doc_phase_agreement", severity="pass",
        message=f"all declaring docs agree on Phase {agreed}",
    )]


def _check_archive_claim_missing(root: Path) -> list[AuditFinding]:
    """Flag claims that a phase was archived to ``tasks/archive/phase-N/`` when
    that directory does not exist under the repo root.

    Scans backlog.md and the current_focus ledger for archive claims.
    """
    doc = "cross_doc"
    claims: set[int] = set()  # phase numbers claimed as archived
    for rel_path in (_BACKLOG_PATH, _CURRENT_FOCUS_PATH):
        path = root / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for m in _ARCHIVE_CLAIM_RE.finditer(text):
            # A literal "phase-N" with a concrete number is a claim; the
            # "phase-{N}" template placeholder in prose has no digit and is
            # skipped by the \d+ match.
            claims.add(int(m.group(1)))

    if not claims:
        return [AuditFinding(
            doc=doc, check_id="archive_claim_missing", severity="pass",
            message="no task-archive claims found — skipped",
        )]

    missing = sorted(
        n for n in claims if not (root / "tasks" / "archive" / f"phase-{n}").is_dir()
    )
    if missing:
        return [
            AuditFinding(
                doc=doc, check_id="archive_claim_missing", severity="warning",
                message=(
                    f"archive claim points to a missing directory: "
                    f"tasks/archive/phase-{n}/"
                ),
                remediation=(
                    f"create tasks/archive/phase-{n}/ (grain phase close) or "
                    f"correct the archive claim"
                ),
            )
            for n in missing
        ]

    return [AuditFinding(
        doc=doc, check_id="archive_claim_missing", severity="pass",
        message=f"all {len(claims)} archive claim(s) resolve to existing directories",
    )]


def _check_task_id_counter_drift(root: Path) -> list[AuditFinding]:
    """Flag a registered doc whose declared "highest/next task ID" no longer
    matches the real maximum TASK-#### across ``tasks/`` and ``tasks/archive/``.

    Passes (n/a) when no doc declares such a counter.
    """
    doc = "cross_doc"
    declarations = _collect_task_id_declarations(root)
    if not declarations:
        return [AuditFinding(
            doc=doc, check_id="task_id_counter_drift", severity="pass",
            message="no 'highest/next task ID' declaration found — skipped",
        )]

    actual_max = _max_task_id_on_disk(root)
    if actual_max is None:
        return [AuditFinding(
            doc=doc, check_id="task_id_counter_drift", severity="pass",
            message="no TASK-#### packets on disk — skipped",
        )]

    findings: list[AuditFinding] = []
    for label, declared in declarations:
        if declared != actual_max:
            findings.append(AuditFinding(
                doc=doc, check_id="task_id_counter_drift", severity="warning",
                message=(
                    f"{label} declares highest/next task ID TASK-{declared:04d} "
                    f"but the real maximum on disk is TASK-{actual_max:04d}"
                ),
                remediation=(
                    f"update {label} to reflect TASK-{actual_max:04d} "
                    f"(the actual max across tasks/ and tasks/archive/)"
                ),
            ))

    if findings:
        return findings
    return [AuditFinding(
        doc=doc, check_id="task_id_counter_drift", severity="pass",
        message=f"declared task ID counter matches disk max TASK-{actual_max:04d}",
    )]


def _declared_phase_number(text: str) -> str:
    """Return the active/current phase number a doc declares, or "".

    Tries explicit "Active phase"/"Current Phase"/"Phase:" markers first, then
    falls back to the shared _extract_current_phase parser (which handles the
    "## Current Phase" heading + following "Phase N" line in current_focus.md).
    """
    for line in text.splitlines():
        for pattern in _DECLARED_PHASE_RES:
            m = pattern.search(line)
            if m:
                return m.group(1)
    phase_line = _extract_current_phase(text)
    if phase_line:
        m = re.search(r"Phase\s+(\d+)", phase_line)
        if m:
            return m.group(1)
    return ""


def _collect_task_id_declarations(root: Path) -> list[tuple[str, int]]:
    """Scan registered docs for "highest/next task ID: TASK-####" declarations.

    Returns (doc_label, declared_number) pairs. Reads the doc set from the
    manifest (canonical/working/runtime), plus the well-known runtime agent
    docs (CLAUDE.md / AGENTS.md) which carry these counters but may not be
    individually registered.
    """
    candidates: list[str] = []
    manifest_path = root / _MANIFEST_PATH
    if manifest_path.exists():
        try:
            import yaml  # type: ignore
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            for entry in _collect_manifest_doc_entries(manifest):
                p = entry.get("path", "")
                if p and not p.endswith("/"):
                    candidates.append(p)
        except Exception:
            pass
    for extra in ("docs/runtime/CLAUDE.md", "docs/runtime/AGENTS.md",
                  "CLAUDE.md", "AGENTS.md"):
        if extra not in candidates:
            candidates.append(extra)

    declarations: list[tuple[str, int]] = []
    seen: set[str] = set()
    for rel_path in candidates:
        if rel_path in seen:
            continue
        seen.add(rel_path)
        path = root / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for m in _TASK_COUNTER_RE.finditer(text):
            declarations.append((rel_path, int(m.group(1))))
    return declarations


def _max_task_id_on_disk(root: Path) -> int | None:
    """Return the highest TASK-#### number found across tasks/ and
    tasks/archive/ (packet directory names), or None if none exist."""
    tasks_root = root / "tasks"
    if not tasks_root.exists():
        return None
    max_id: int | None = None
    for path in tasks_root.rglob("*"):
        if not path.is_dir():
            continue
        m = _TASK_ID_NUM_RE.search(path.name)
        if m:
            num = int(m.group(1))
            if max_id is None or num > max_id:
                max_id = num
    return max_id


# ── Corpus staleness signals ──────────────────────────────────────────────────
#
# Design ruling (2026-08): labels are claims, not truth. A canonical doc can be
# stale, and a working doc can be MORE current than the canon it overlaps. No
# signal below assumes canon=fresh: reference rot and subject drift apply to
# canon; verification age nags canon that is long-UNVERIFIED (not long-unedited);
# supersession surfaces working-newer-than-canon conflicts as queue items and
# never auto-rules.
#
# Rot and drift always evaluate against the repo state at audit time — the
# corpus cache stores extraction (links, refs, stamps), never verdicts.

def _check_corpus(
    root: Path,
    config: AuditConfig,
    signals: set[str],
    progress=None,
) -> list[AuditFinding]:
    from grain.services.docs_corpus import (
        last_commit_dates,
        load_corpus,
        load_git_commit_index,
    )

    def _tick(msg: str) -> None:
        if progress is not None:
            progress(msg)

    manifest = _safe_manifest(root)
    _tick("scanning docs corpus…")
    corpus = load_corpus(root, manifest=manifest, use_cache=True)

    # One batched git-history walk serves every git-backed signal (dates +
    # churn) — cost scales with history once, not with docs × references.
    git_index = None
    git_dates: dict = {}
    if signals & {"subject_drift", "supersession", "verification_age", "stale_drafts"}:
        _tick("reading git history…")
        git_index = load_git_commit_index(root)
        if git_index is not None:
            git_dates = last_commit_dates(git_index)

    findings: list[AuditFinding] = []
    if "reference_rot" in signals:
        _tick("checking reference rot…")
        findings.extend(_check_reference_rot(root, corpus, manifest))
    if "subject_drift" in signals:
        _tick("checking subject drift (git history)…")
        findings.extend(_check_subject_drift(root, corpus, config, git_index, git_dates))
    if "supersession" in signals:
        _tick("checking supersession pressure…")
        findings.extend(_check_supersession(root, corpus, config, manifest, git_dates))
    if "verification_age" in signals:
        _tick("checking verification age…")
        findings.extend(_check_verification_age(corpus, config, git_dates))
    if "orphans" in signals:
        findings.extend(_check_orphans(corpus, manifest))
    if "duplicate_topics" in signals:
        findings.extend(_check_duplicate_topics(corpus))
    if "stale_drafts" in signals:
        findings.extend(_check_stale_drafts(corpus, config, git_dates))
    if "manifest_reconciliation" in signals:
        findings.extend(_check_manifest_reconciliation(corpus, manifest))
    return findings


def _safe_manifest(root: Path) -> dict:
    manifest_path = root / _MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _registered_paths(manifest: dict) -> set[str]:
    return {
        e.get("path", "").rstrip("/")
        for e in _collect_manifest_doc_entries(manifest)
        if e.get("path")
    }


def _doc_targets(doc) -> list[str]:
    """All repo-relative paths a doc cites (links + path refs), deduplicated."""
    seen: set[str] = set()
    targets: list[str] = []
    for t in list(doc.resolved_links) + list(doc.path_refs):
        if t and t not in seen:
            seen.add(t)
            targets.append(t)
    return targets


# a. Reference rot — objective staleness; applies to canon too.

def _check_reference_rot(root: Path, corpus: list, manifest: dict) -> list[AuditFinding]:
    from grain.services.docs_corpus import external_roots_from_manifest

    # Cross-repo citations resolve against registered external roots by name
    # prefix: `labs/docs/x.md` checks <external root 'labs'>/docs/x.md.
    ext_roots = dict(external_roots_from_manifest(root, manifest))

    def _exists(doc, target: str) -> bool:
        if (root / target).exists():
            return True
        # doc-relative citations: `canonical/x.md` written from docs/working/
        # resolves via the doc's own directory or its parent tree
        if (doc.abs_path.parent / target).exists():
            return True
        if (doc.abs_path.parent.parent / target).exists():
            return True
        # cross-repo citations resolve against external roots by name prefix
        head, _, tail = target.partition("/")
        if tail and head in ext_roots and (ext_roots[head] / tail).exists():
            return True
        return False

    findings: list[AuditFinding] = []
    checked = 0
    for doc in corpus:
        if doc.layer == "archive" or doc.root_name:
            continue  # archived docs are frozen history; external roots are search-only
        checked += 1
        missing = [t for t in _doc_targets(doc) if not _exists(doc, t)]
        if missing:
            shown = ", ".join(missing[:3])
            more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
            findings.append(AuditFinding(
                doc="reference_rot", check_id="reference_rot", severity="warning",
                message=f"{doc.rel_path}: cites missing path(s): {shown}{more}",
                remediation=f"update or remove the dead references in {doc.rel_path}",
            ))
    if not findings:
        findings.append(AuditFinding(
            doc="reference_rot", check_id="reference_rot", severity="pass",
            message=f"all cited paths resolve ({checked} docs checked)",
        ))
    return findings


# b. Subject drift — the world moved, the doc didn't. Git-backed; degrades
#    gracefully outside a repo.

def _check_subject_drift(
    root: Path, corpus: list, config: AuditConfig, git_index, git_dates: dict
) -> list[AuditFinding]:
    from grain.services.docs_corpus import churn_since

    if git_index is None:
        return [AuditFinding(
            doc="subject_drift", check_id="subject_drift", severity="pass",
            message="not a git repository — subject drift skipped",
        )]

    findings: list[AuditFinding] = []
    for doc in corpus:
        if doc.layer == "archive" or doc.root_name:
            continue
        targets = [t for t in _doc_targets(doc) if (root / t).exists()]
        if not targets:
            continue
        doc_date = _doc_date(doc, git_dates)
        if doc_date is None:
            continue
        churn = churn_since(git_index, set(targets), doc_date)
        if churn >= config.subject_drift_commits:
            shown = ", ".join(targets[:3])
            more = f", +{len(targets) - 3} more" if len(targets) > 3 else ""
            findings.append(AuditFinding(
                doc="subject_drift", check_id="subject_drift", severity="warning",
                message=(
                    f"{doc.rel_path}: referenced paths churned in {churn} commit(s) "
                    f"since the doc last changed ({doc_date}) — {shown}{more}"
                ),
                remediation=f"reread {doc.rel_path} against the current code, then grain docs verify {doc.rel_path}",
            ))
    if not findings:
        findings.append(AuditFinding(
            doc="subject_drift", check_id="subject_drift", severity="pass",
            message=f"no doc's referenced paths churned ≥{config.subject_drift_commits} commits",
        ))
    return findings


# c. Supersession pressure — a working doc newer than an overlapping canon doc
#    becomes a PROMOTION CANDIDATE queue item. The audit never auto-rules.

def _title_tokens(title: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", title.lower()) if t}


def _titles_overlap(a: str, b: str, threshold: float = 0.5) -> bool:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= threshold


def _manifest_topics(manifest: dict) -> dict[str, set[str]]:
    """path -> topic tags, from optional ``topics:`` lists on manifest entries."""
    topics: dict[str, set[str]] = {}
    for entry in _collect_manifest_doc_entries(manifest):
        raw = entry.get("topics")
        if isinstance(raw, list) and raw:
            topics[entry.get("path", "")] = {str(t).lower() for t in raw}
    return topics


def _doc_date(doc, git_dates: dict):
    """Doc recency: last git commit date when available, else mtime.

    Git wins because mtime is fragile (clones and copies reset it); an
    uncommitted edit is transient and will be seen on the post-commit run."""
    d = git_dates.get(doc.rel_path)
    if d is not None:
        return d
    return doc.last_modified.date() if doc.last_modified else None


def _check_supersession(
    root: Path, corpus: list, config: AuditConfig, manifest: dict, git_dates: dict
) -> list[AuditFinding]:
    canon = [d for d in corpus if d.layer == "canonical" and not d.root_name]
    working = [
        d for d in corpus
        if d.layer == "working" and not d.root_name
        and d.abs_path.name not in _WORKFLOW_DOC_NAMES
        and not d.is_tombstone
    ]
    topics = _manifest_topics(manifest)
    inbound: dict[str, int] = {}
    for doc in corpus:
        for target in doc.resolved_links:
            inbound[target] = inbound.get(target, 0) + 1

    findings: list[AuditFinding] = []
    for w in working:
        w_date = _doc_date(w, git_dates)
        if w_date is None:
            continue
        w_targets = set(_doc_targets(w))
        for c in canon:
            c_date = _doc_date(c, git_dates)
            if c_date is None or w_date <= c_date:
                continue
            overlap = (
                _titles_overlap(w.title, c.title)
                or bool(w_targets & set(_doc_targets(c)))
                or bool(topics.get(w.rel_path, set()) & topics.get(c.rel_path, set()))
            )
            if not overlap:
                continue
            refs = inbound.get(w.rel_path, 0)
            findings.append(AuditFinding(
                doc="supersession", check_id="supersession", severity="warning",
                message=(
                    f"PROMOTION CANDIDATE: working {w.rel_path} (modified {w_date}, "
                    f"{refs} inbound ref(s)) may supersede canon {c.rel_path} "
                    f"(modified {c_date})"
                ),
                remediation=(
                    f"review both, then grain docs promote {w.rel_path} "
                    f"--into {c.rel_path} — or dismiss by updating the canon doc"
                ),
            ))
    if not findings:
        findings.append(AuditFinding(
            doc="supersession", check_id="supersession", severity="pass",
            message="no working doc is newer than an overlapping canonical doc",
        ))
    return findings


# d. Verification age — canon staleness is long-UNVERIFIED, not long-unedited.

def _check_verification_age(
    corpus: list, config: AuditConfig, git_dates: dict
) -> list[AuditFinding]:
    if config.canon_unverified_days <= 0:
        return [AuditFinding(
            doc="verification_age", check_id="verification_age", severity="pass",
            message="verification-age nag disabled (canon_unverified_days ≤ 0)",
        )]
    today = datetime.now(tz=timezone.utc).date()
    findings: list[AuditFinding] = []
    for doc in corpus:
        if doc.layer != "canonical" or doc.root_name or doc.is_tombstone:
            continue
        if doc.last_verified is not None:
            age = (today - doc.last_verified).days
            if age > config.canon_unverified_days:
                findings.append(AuditFinding(
                    doc="verification_age", check_id="verification_age", severity="warning",
                    message=(
                        f"{doc.rel_path}: last verified {age} days ago "
                        f"(threshold: {config.canon_unverified_days})"
                    ),
                    remediation=f"reread it, then grain docs verify {doc.rel_path}",
                ))
        else:
            doc_date = _doc_date(doc, git_dates)
            mod_age = (today - doc_date).days if doc_date else None
            if mod_age is not None and mod_age > config.canon_unverified_days:
                findings.append(AuditFinding(
                    doc="verification_age", check_id="verification_age", severity="warning",
                    message=(
                        f"{doc.rel_path}: never verified and untouched for {mod_age} days "
                        f"(threshold: {config.canon_unverified_days})"
                    ),
                    remediation=f"reread it, then grain docs verify {doc.rel_path}",
                ))
    if not findings:
        findings.append(AuditFinding(
            doc="verification_age", check_id="verification_age", severity="pass",
            message="all canonical docs verified (or modified) recently enough",
        ))
    return findings


# Classics — orphans, duplicate-topic clusters, stale drafts, reconciliation.

def _check_orphans(corpus: list, manifest: dict) -> list[AuditFinding]:
    registered = _registered_paths(manifest)
    linked: set[str] = set()
    for doc in corpus:
        linked.update(doc.resolved_links)

    findings: list[AuditFinding] = []
    for doc in corpus:
        if doc.layer not in ("canonical", "working") or doc.root_name or doc.is_tombstone:
            continue
        if doc.abs_path.name in _WORKFLOW_DOC_NAMES:
            continue
        if doc.rel_path in registered or doc.rel_path in linked:
            continue
        findings.append(AuditFinding(
            doc="orphans", check_id="orphans", severity="warning",
            message=f"{doc.rel_path}: no inbound links and not in the manifest",
            remediation=(
                f"register it in docs_manifest.yaml, link it from another doc, "
                f"or grain docs archive {doc.rel_path}"
            ),
        ))
    if not findings:
        findings.append(AuditFinding(
            doc="orphans", check_id="orphans", severity="pass",
            message="no orphaned docs (all linked or registered)",
        ))
    return findings


def _check_duplicate_topics(corpus: list) -> list[AuditFinding]:
    docs = [
        d for d in corpus
        if d.layer in ("canonical", "working") and not d.root_name and d.title
        and d.abs_path.name not in _WORKFLOW_DOC_NAMES and not d.is_tombstone
    ]
    # Union-find over title-similar pairs
    parent = {d.rel_path: d.rel_path for d in docs}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            if _titles_overlap(a.title, b.title, threshold=0.6):
                parent[find(a.rel_path)] = find(b.rel_path)

    clusters: dict[str, list[str]] = {}
    for d in docs:
        clusters.setdefault(find(d.rel_path), []).append(d.rel_path)

    findings: list[AuditFinding] = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        findings.append(AuditFinding(
            doc="duplicate_topics", check_id="duplicate_topics", severity="warning",
            message=f"possible duplicate topic cluster: {', '.join(sorted(members))}",
            remediation="consolidate into one doc; archive or promote the others",
        ))
    if not findings:
        findings.append(AuditFinding(
            doc="duplicate_topics", check_id="duplicate_topics", severity="pass",
            message="no duplicate-topic clusters detected",
        ))
    return findings


def _check_stale_drafts(
    corpus: list, config: AuditConfig, git_dates: dict
) -> list[AuditFinding]:
    if config.draft_archive_days <= 0:
        return [AuditFinding(
            doc="stale_drafts", check_id="stale_drafts", severity="pass",
            message="stale-draft check disabled (draft_archive_days ≤ 0)",
        )]
    today = datetime.now(tz=timezone.utc).date()
    findings: list[AuditFinding] = []
    for doc in corpus:
        if doc.layer != "working" or doc.root_name or doc.is_tombstone:
            continue
        if doc.abs_path.name in _WORKFLOW_DOC_NAMES:
            continue
        doc_date = _doc_date(doc, git_dates)
        if doc_date is None:
            continue
        age = (today - doc_date).days
        if age > config.draft_archive_days:
            findings.append(AuditFinding(
                doc="stale_drafts", check_id="stale_drafts", severity="warning",
                message=f"{doc.rel_path}: untouched for {age} days (threshold: {config.draft_archive_days})",
                remediation=f"grain docs archive {doc.rel_path} (or promote it if it superseded canon)",
            ))
    if not findings:
        findings.append(AuditFinding(
            doc="stale_drafts", check_id="stale_drafts", severity="pass",
            message="no working docs old enough to archive",
        ))
    return findings


def _check_manifest_reconciliation(corpus: list, manifest: dict) -> list[AuditFinding]:
    """Corpus docs absent from the manifest. (The inverse — manifest entries
    pointing at missing files — is the structural ``registered_doc_missing``
    check, which predates the corpus signals.)"""
    if not manifest:
        return [AuditFinding(
            doc="manifest_reconciliation", check_id="manifest_unregistered", severity="pass",
            message="no manifest — reconciliation skipped",
        )]
    registered = _registered_paths(manifest)
    findings: list[AuditFinding] = []
    for doc in corpus:
        if doc.layer not in ("canonical", "working") or doc.root_name or doc.is_tombstone:
            continue
        if doc.rel_path not in registered:
            findings.append(AuditFinding(
                doc="manifest_reconciliation", check_id="manifest_unregistered", severity="warning",
                message=f"{doc.rel_path}: present on disk but not registered in docs_manifest.yaml",
                remediation=f"add a {doc.layer} entry for it (or grain docs archive {doc.rel_path})",
            ))
    if not findings:
        findings.append(AuditFinding(
            doc="manifest_reconciliation", check_id="manifest_unregistered", severity="pass",
            message="every corpus doc is registered in the manifest",
        ))
    return findings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_current_task(path: Path) -> dict:
    result: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Task ID:"):
            result["task_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("Task Path:"):
            result["task_path"] = line.split(":", 1)[1].strip()
        elif line.startswith("Status:"):
            result["status"] = line.split(":", 1)[1].strip()
    return result


def _resolve_packet(root: Path, task_id: str, task_path: str) -> Path | None:
    if task_path and task_path not in ("none", "(unset)"):
        candidate = root / task_path.rstrip("/")
        if candidate.is_dir():
            return candidate
    tasks_root = root / "tasks"
    if not tasks_root.exists():
        return None
    return _find_packet_by_id(tasks_root, task_id)


def _find_packet_by_id(tasks_root: Path, task_id: str) -> Path | None:
    if not tasks_root.exists():
        return None
    for d in tasks_root.iterdir():
        if d.is_dir() and task_id in d.name:
            return d
    return None


def _parse_backlog_phases(text: str) -> list[dict]:
    """Parse backlog.md into a list of phase dicts with task lists."""
    _PHASE_RE = re.compile(r"^##\s+(?:\d+\.\s+)?(Phase\s+\d+[^#\n]*?)(\s*✓\s*CLOSED)?$")
    _TASK_RE = re.compile(r"^###\s+(P\d+-T\d+)\s+—")
    _STATUS_RE = re.compile(r"^-\s+\*\*Status:\*\*\s*(\S+)")
    _TASK_ID_RE = re.compile(r"^-\s+\*\*TASK-ID:\*\*\s*(TASK-\d+)")
    _PHASE_STATUS_RE = re.compile(r"^>\s+\*\*Status:\*\*\s*(\S+)")

    phases: list[dict] = []
    current_phase: dict | None = None
    current_task: dict | None = None

    def flush_task():
        if current_task and current_phase:
            current_phase["tasks"].append(current_task.copy())

    def flush_phase():
        flush_task()
        if current_phase:
            phases.append(current_phase.copy())

    for line in text.splitlines():
        pm = _PHASE_RE.match(line)
        if pm:
            flush_phase()
            current_phase = {
                "name": pm.group(1).strip(),
                "closed": bool(pm.group(2)),
                "status": "",
                "tasks": [],
            }
            current_task = None
            continue

        if current_phase is None:
            continue

        ps = _PHASE_STATUS_RE.match(line)
        if ps:
            current_phase["status"] = ps.group(1).lower().rstrip(".,")
            continue

        tm = _TASK_RE.match(line)
        if tm:
            flush_task()
            current_task = {"ref": tm.group(1), "status": "", "task_id": ""}
            continue

        if current_task is not None:
            sm = _STATUS_RE.match(line)
            if sm:
                current_task["status"] = sm.group(1).lower().rstrip(".,")
                continue
            id_m = _TASK_ID_RE.match(line)
            if id_m:
                current_task["task_id"] = id_m.group(1)

    flush_phase()
    return phases


def _extract_current_phase(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Phase ") or "Phase " in line:
            m = re.search(r"Phase\s+\d+", line)
            if m:
                return line.strip()
    # also try "## Current Phase" section
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "## Current Phase" in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line:
                return next_line
    return ""


def _extract_priority_task_refs(text: str) -> list[str]:
    priorities_section = ""
    in_section = False
    for line in text.splitlines():
        if "## Immediate Priorities" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") and "Immediate Priorities" not in line:
                break
            priorities_section += line + "\n"
    return _TASK_REF_RE.findall(priorities_section)


def _get_task_status_in_backlog(backlog_text: str, task_ref: str) -> str:
    _TASK_HEADING_RE = re.compile(rf"^###\s+{re.escape(task_ref)}\s+—")
    _STATUS_RE = re.compile(r"^-\s+\*\*Status:\*\*\s*(\S+)")
    found = False
    for line in backlog_text.splitlines():
        if _TASK_HEADING_RE.match(line):
            found = True
            continue
        if found:
            if line.startswith("### ") or line.startswith("## "):
                break
            m = _STATUS_RE.match(line)
            if m:
                return m.group(1).lower().rstrip(".,")
    return ""


def _collect_manifest_doc_entries(manifest: dict) -> list[dict]:
    entries: list[dict] = []
    for layer in ("canonical", "working", "runtime"):
        for entry in manifest.get(layer, []):
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def _is_template_only(content: str) -> bool:
    """Return True if file has no substantive content beyond heading lines."""
    substantive = [
        line for line in content.splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("<!--")
    ]
    return len(substantive) == 0


def _clear_current_task(root: Path) -> None:
    path = root / _CURRENT_TASK_PATH
    path.write_text(
        "# Current Task\n\nTask ID: none\nTask Path: none\nStatus: unset\n",
        encoding="utf-8",
    )
