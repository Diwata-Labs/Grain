# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Task service — packet directory creation and lifecycle operations."""

import re
from pathlib import Path

from grain.adapters.manifest import load_completion_policy
from grain.cli.output import CommandResult
from grain.domain.packets import (
    ALLOWED_TRANSITIONS,
    TASK_ID_PATTERN,
    PacketRecord,
    find_packet_dir,
    next_task_id,
    read_packet_record,
    write_packet_status,
)
from grain.templates.loader import get_template
from grain.validators.packet_validator import (
    validate_closure,
    validate_packet,
    validate_status_transition,
)

_REQUIRED_TEMPLATES = [
    "tasks/task.md",
    "tasks/context.md",
    "tasks/plan.md",
    "tasks/deliverable_spec.md",
]

_SIMPLE_TEMPLATES = [
    "tasks/task.md",
    "tasks/results.md",
]

# P<phase>-T<num> prefix of a packet directory name (before the TASK-#### segment).
_TASK_REF_PATTERN = re.compile(r"^(P\d+-T\d+)-TASK-\d+")


def _canonical_task_ref(identifier: str) -> str:
    """Reduce a packet identifier to its bare TASK-#### id when possible.

    Accepts either a bare id ("TASK-0001") or a full packet directory name
    ("P1-T01-TASK-0001") and returns "TASK-0001". Any other string is returned
    stripped and unchanged.
    """
    identifier = identifier.strip()
    match = TASK_ID_PATTERN.search(identifier)
    return match.group(0) if match else identifier


def resolve_task_identifier(positional: str | None, option: str | None) -> str | None:
    """Resolve a task id from an optional positional and/or the --id option.

    The positional may be a bare TASK-#### id or a full packet directory name
    (as printed by ``grain task list``). Returns the canonical id to use for
    packet lookup, or None when neither was supplied (callers keep their prior
    behavior in that case).

    Raises:
        ValueError: when both selectors are given and name different tasks.
    """
    if positional and option:
        if _canonical_task_ref(positional) != _canonical_task_ref(option):
            raise ValueError(
                f"positional id '{positional}' and --id '{option}' name different tasks"
            )
        return _canonical_task_ref(option)
    if positional:
        return _canonical_task_ref(positional)
    if option:
        return option
    return None


def _sync_backlog_status(
    root: Path, packet_dir: Path, new_status: str, files_updated: list[str]
) -> None:
    """Sync docs/working/backlog.md for this packet's task ref to ``new_status``.

    Both entering (start) and leaving (close) a packet must keep the backlog in
    step, so ``grain workflow reconcile`` reports no drift immediately afterward.
    No-op when the packet dir name carries no ``P#-T#`` ref or the backlog is
    absent. Appends the backlog path to ``files_updated`` only when it changed.
    """
    ref_match = _TASK_REF_PATTERN.match(packet_dir.name)
    backlog_path = root / "docs" / "working" / "backlog.md"
    if not (ref_match and backlog_path.exists()):
        return

    from grain.services.reconcile_service import _update_backlog_task_status

    text = backlog_path.read_text(encoding="utf-8")
    new_text = _update_backlog_task_status(text, ref_match.group(1), new_status)
    if new_text != text:
        backlog_path.write_text(new_text, encoding="utf-8")
        files_updated.append("docs/working/backlog.md")


def create_packet_directory(
    root: Path, phase: int, task_num: int, title: str = "", simple: bool = False
) -> CommandResult:
    """Create a new packet directory under tasks/ with required template files.

    Allocates the next available TASK-#### ID, constructs a P<N>-T<NN>-TASK-####
    directory name, creates the directory, and populates it with template files.

    In normal mode: task.md, context.md, plan.md, deliverable_spec.md.
    In simple mode (--simple): task.md + results.md only. Suitable for small,
    mechanical tasks where planning files add overhead without value.

    Returns:
        CommandResult with ok=True, task_id set, and files_created populated on
        success. ok=False with errors on failure.
    """
    tasks_root = root / "tasks"
    task_id = next_task_id(tasks_root)
    dir_name = f"P{phase}-T{task_num:02d}-{task_id}"
    packet_dir = tasks_root / dir_name

    if packet_dir.exists():
        return CommandResult(
            ok=False,
            command="task create",
            errors=[f"packet directory already exists: {packet_dir.relative_to(root)}"],
        )

    packet_dir.mkdir(parents=True)

    files_created = [str(packet_dir.relative_to(root))]

    templates = _SIMPLE_TEMPLATES if simple else _REQUIRED_TEMPLATES
    for template_name in templates:
        content = get_template(template_name, root)
        filename = Path(template_name).name
        if filename == "task.md":
            content = content.replace("TASK-####", task_id)
            if title:
                content = content.replace("[Title]", title)
            if simple:
                content = content.replace(
                    "- **Status:** draft",
                    "- **Status:** draft\n- **Mode:** simple",
                )
        dest = packet_dir / filename
        dest.write_text(content, encoding="utf-8")
        files_created.append(str(dest.relative_to(root)))

    return CommandResult(
        ok=True,
        command="task create",
        repo=str(root),
        task_id=task_id,
        files_created=files_created,
    )


def list_packets(root: Path) -> tuple[CommandResult, list[PacketRecord]]:
    """Scan tasks/ and return a sorted list of PacketRecords.

    Directories without a valid TASK-#### segment are ignored.
    Directories missing task.md are skipped with a warning.

    Returns:
        (CommandResult, list[PacketRecord]) — result is ok=True even when
        tasks/ is empty or absent. Warnings are populated for unreadable packets.
    """
    tasks_root = root / "tasks"

    if not tasks_root.exists():
        return CommandResult(ok=True, command="task list", repo=str(root)), []

    packet_dirs = sorted(
        (d for d in tasks_root.iterdir() if d.is_dir() and TASK_ID_PATTERN.search(d.name)),
        key=lambda d: int(TASK_ID_PATTERN.search(d.name).group(1)),
    )

    records: list[PacketRecord] = []
    warnings: list[str] = []

    for packet_dir in packet_dirs:
        try:
            records.append(read_packet_record(packet_dir))
        except FileNotFoundError:
            warnings.append(f"{packet_dir.name}: task.md not found, skipped")

    return CommandResult(
        ok=True,
        command="task list",
        repo=str(root),
        warnings=warnings,
    ), records


_ALL_PACKET_FILES = (
    "task.md",
    "context.md",
    "plan.md",
    "deliverable_spec.md",
    "results.md",
    "handoff.md",
)


def validate_one_packet(root: Path, task_id: str) -> CommandResult:
    """Validate required files and metadata for one packet.

    Returns ok=False with errors when the packet is not found or fails validation.
    """
    packet_dir = find_packet_dir(root / "tasks", task_id)
    if packet_dir is None:
        return CommandResult(
            ok=False,
            command="task validate",
            errors=[f"packet '{task_id}' not found"],
        )
    errors = validate_packet(packet_dir)
    return CommandResult(
        ok=not errors,
        command="task validate",
        repo=str(root),
        task_id=task_id,
        errors=errors,
    )


def validate_all_packets(root: Path) -> CommandResult:
    """Validate all packets found under tasks/.

    Each error is prefixed with the packet directory name.
    Returns ok=True when tasks/ is empty or absent.
    """
    tasks_root = root / "tasks"
    if not tasks_root.exists():
        return CommandResult(ok=True, command="task validate", repo=str(root))

    packet_dirs = sorted(
        (d for d in tasks_root.iterdir() if d.is_dir() and TASK_ID_PATTERN.search(d.name)),
        key=lambda d: int(TASK_ID_PATTERN.search(d.name).group(1)),
    )

    all_errors: list[str] = []
    for packet_dir in packet_dirs:
        for err in validate_packet(packet_dir):
            all_errors.append(f"{packet_dir.name}: {err}")

    return CommandResult(
        ok=not all_errors,
        command="task validate",
        repo=str(root),
        errors=all_errors,
    )


def close_packet(root: Path, task_id: str) -> CommandResult:
    """Attempt closure of a packet after running all closure validation checks.

    Runs validate_closure(); if all checks pass, transitions status to 'done'.

    Returns:
        CommandResult with ok=True and status='done' on success.
        ok=False with errors when packet not found or closure validation fails.
    """
    packet_dir = find_packet_dir(root / "tasks", task_id)

    if packet_dir is None:
        return CommandResult(
            ok=False,
            command="task close",
            errors=[f"packet '{task_id}' not found"],
        )

    errors = validate_closure(packet_dir, policy=load_completion_policy(root))
    if errors:
        return CommandResult(
            ok=False,
            command="task close",
            errors=errors,
        )

    results_path = packet_dir / "results.md"
    if results_path.exists():
        _finalize_results_closure(results_path)

    write_packet_status(packet_dir, "done")

    files_updated = [str((packet_dir / "task.md").relative_to(root))]
    if results_path.exists():
        files_updated.insert(0, str(results_path.relative_to(root)))

    _sync_backlog_status(root, packet_dir, "done", files_updated)

    # Side-band telemetry (opt-in, never raises, never alters control flow or
    # timing). emit_built guards builder construction too.
    from grain.services.telemetry_service import emit_built, make_task_close_event
    emit_built(root, make_task_close_event, task_id)

    return CommandResult(
        ok=True,
        command="task close",
        repo=str(root),
        task_id=task_id,
        status="done",
        files_updated=files_updated,
    )


def quick_close_packet(
    root: Path, task_id: str, summary: str, files: list[str] | None = None
) -> CommandResult:
    """Minimal closure for conversational/voice workflows.

    Writes a stripped-down results.md with the provided summary (and optional
    file list), then transitions packet status to 'done'.  Does NOT require
    handoff.md or efficiency metrics — those are optional for quick closures.

    Returns:
        CommandResult with ok=True and status='done' on success.
        ok=False with errors when packet not found.
    """
    packet_dir = find_packet_dir(root / "tasks", task_id)

    if packet_dir is None:
        return CommandResult(
            ok=False,
            command="task close",
            errors=[f"packet '{task_id}' not found"],
        )

    results_path = packet_dir / "results.md"
    files_section = ""
    if files:
        file_lines = "\n".join(f"- {f}" for f in files)
        files_section = f"\n\n## Files Changed\n\n{file_lines}"

    results_content = (
        f"# Results: {task_id}\n\n"
        "<!-- Quick closure generated by grain task close --quick -->\n\n"
        "## Packet State\n"
        "- **Current Task Status:** done\n"
        "- **Review Readiness:** approved\n"
        "- **Recommended Next Status:** done\n\n"
        "## Summary\n\n"
        f"{summary}\n"
        f"{files_section}\n\n"
        "## User Review\n"
        "- **State:** approved\n"
        "- **Summary:** Quick closure accepted by operator.\n"
        "- **Resolution Mode:** close_task\n\n"
        "### Required Fixes\n"
        "- None\n\n"
        "### Open Questions To Log\n"
        "- None\n\n"
        "### Proposal Candidates To Log\n"
        "- None\n\n"
        "### Follow-Ups To Log\n"
        "- None\n\n"
        "### Residual Risks\n"
        "- None\n\n"
        "## Verification Review\n"
        "- **State:** not_run\n"
        "- **Summary:** No verifier configured for quick closure.\n\n"
        "### Findings\n"
        "- None\n\n"
        "## Closure Decision\n"
        "- **Decision:** closed\n"
        "- **Reason:** Closed via grain task close --quick.\n\n"
        "### Closure Blockers\n"
        "- None\n"
    )
    results_path.write_text(results_content, encoding="utf-8")

    write_packet_status(packet_dir, "done")

    files_updated = [str((packet_dir / "task.md").relative_to(root))]
    _sync_backlog_status(root, packet_dir, "done", files_updated)

    # Side-band telemetry (opt-in, never raises, never alters control flow or
    # timing). emit_built guards builder construction too.
    from grain.services.telemetry_service import emit_built, make_task_close_event
    emit_built(root, make_task_close_event, task_id, quick=True)

    return CommandResult(
        ok=True,
        command="task close",
        repo=str(root),
        task_id=task_id,
        status="done",
        files_created=[str(results_path.relative_to(root))],
        files_updated=files_updated,
    )


def update_packet_status(root: Path, task_id: str, new_status: str) -> CommandResult:
    """Validate and apply a status transition for one packet.

    Returns:
        CommandResult with ok=True and status set on success.
        ok=False with errors when packet not found, task.md missing,
        or the transition is not allowed.
    """
    packet_dir = find_packet_dir(root / "tasks", task_id)

    if packet_dir is None:
        return CommandResult(
            ok=False,
            command="task status",
            errors=[f"packet '{task_id}' not found"],
        )

    try:
        record = read_packet_record(packet_dir)
    except FileNotFoundError:
        return CommandResult(
            ok=False,
            command="task status",
            errors=[f"packet '{task_id}': task.md not found"],
        )

    errors = validate_status_transition(record.status, new_status)
    if errors:
        return CommandResult(
            ok=False,
            command="task status",
            errors=[f"{errors[0]}; {_legal_next_hint(record.status)}"] + errors[1:],
        )

    write_packet_status(packet_dir, new_status)

    return CommandResult(
        ok=True,
        command="task status",
        repo=str(root),
        task_id=task_id,
        status=new_status,
        files_updated=[str((packet_dir / "task.md").relative_to(root))],
    )


def _legal_next_hint(from_status: str) -> str:
    """Render a human hint naming the legal next state(s) from ``from_status``."""
    allowed = sorted(ALLOWED_TRANSITIONS.get(from_status, frozenset()))
    if not allowed:
        return f"'{from_status}' is terminal; no transitions allowed"
    return f"legal next state(s) from '{from_status}': {', '.join(allowed)}"


# Legal forward path from each status up to in_progress. Every hop is an
# individually-allowed transition per ALLOWED_TRANSITIONS.
_PATH_TO_IN_PROGRESS: dict[str, list[str]] = {
    "draft": ["ready", "in_progress"],
    "ready": ["in_progress"],
    "blocked": ["ready", "in_progress"],
    "needs_fix": ["in_progress"],
    "review": ["in_progress"],
    "in_progress": [],
}


def start_task(root: Path, task_id: str) -> CommandResult:
    """Transition a packet to in_progress and sync the working docs.

    Walks the legal status chain from the packet's current status up to
    in_progress (e.g. draft -> ready -> in_progress), then syncs the backlog.md
    task status and the current_task.md pointer so ``grain workflow reconcile``
    reports no drift immediately afterward.

    Returns:
        CommandResult with ok=True and status='in_progress' on success.
        ok=False with errors when the packet is not found or its current status
        cannot legally reach in_progress.
    """
    packet_dir = find_packet_dir(root / "tasks", task_id)
    if packet_dir is None:
        return CommandResult(
            ok=False,
            command="task start",
            errors=[f"packet '{task_id}' not found"],
        )

    try:
        record = read_packet_record(packet_dir)
    except FileNotFoundError:
        return CommandResult(
            ok=False,
            command="task start",
            errors=[f"packet '{task_id}': task.md not found"],
        )

    if record.status not in _PATH_TO_IN_PROGRESS:
        return CommandResult(
            ok=False,
            command="task start",
            errors=[
                f"cannot start packet in status '{record.status}'; "
                f"{_legal_next_hint(record.status)}"
            ],
        )

    current = record.status
    for nxt in _PATH_TO_IN_PROGRESS[record.status]:
        step_errors = validate_status_transition(current, nxt)
        if step_errors:  # defensive: the path map is legal by construction
            return CommandResult(ok=False, command="task start", errors=step_errors)
        write_packet_status(packet_dir, nxt)
        current = nxt

    resolved_id = record.id or _canonical_task_ref(task_id)
    files_updated = [str((packet_dir / "task.md").relative_to(root))]

    # ── Sync backlog.md status for this packet's task ref ────────────────────
    _sync_backlog_status(root, packet_dir, "in_progress", files_updated)

    # ── Sync current_task.md pointer ─────────────────────────────────────────
    current_task_path = root / "docs" / "working" / "current_task.md"
    current_task_path.parent.mkdir(parents=True, exist_ok=True)
    current_task_path.write_text(
        "# Current Task\n\n"
        f"Task ID: {resolved_id}\n"
        f"Task Path: {packet_dir.relative_to(root)}/\n"
        "Status: in_progress\n",
        encoding="utf-8",
    )
    files_updated.append("docs/working/current_task.md")

    return CommandResult(
        ok=True,
        command="task start",
        repo=str(root),
        task_id=resolved_id,
        status="in_progress",
        files_updated=files_updated,
    )


def show_packet(
    root: Path, task_id: str
) -> tuple[CommandResult, PacketRecord | None, dict[str, bool]]:
    """Return metadata and file inventory for one packet.

    Returns:
        (CommandResult, PacketRecord | None, file_inventory)
        file_inventory maps each packet filename to True (present) or False (absent).
        On failure, CommandResult.ok is False and record is None.
    """
    tasks_root = root / "tasks"
    packet_dir = find_packet_dir(tasks_root, task_id)

    if packet_dir is None:
        return (
            CommandResult(
                ok=False,
                command="task show",
                errors=[f"packet '{task_id}' not found"],
            ),
            None,
            {},
        )

    try:
        record = read_packet_record(packet_dir)
    except FileNotFoundError:
        return (
            CommandResult(
                ok=False,
                command="task show",
                errors=[f"packet '{task_id}': task.md not found"],
            ),
            None,
            {},
        )

    inventory = {name: (packet_dir / name).exists() for name in _ALL_PACKET_FILES}

    return (
        CommandResult(ok=True, command="task show", repo=str(root), task_id=task_id),
        record,
        inventory,
    )


_CLOSURE_DECISION_LINE = re.compile(r"(^- \*\*Decision:\*\*\s*).*$", re.MULTILINE)
_CLOSURE_REASON_LINE = re.compile(r"(^- \*\*Reason:\*\*\s*).*$", re.MULTILINE)
_CLOSURE_BLOCKERS_SECTION = re.compile(
    r"(### Closure Blockers\n)(.*?)(?=\n## |\Z)",
    re.DOTALL,
)


def _finalize_results_closure(results_path: Path) -> None:
    text = results_path.read_text(encoding="utf-8")
    if "## Closure Decision" not in text:
        text = text.rstrip() + (
            "\n\n## Closure Decision\n"
            "- **Decision:** closed\n"
            "- **Reason:** Closed via grain task close.\n\n"
            "### Closure Blockers\n"
            "- None\n"
        )
        results_path.write_text(text, encoding="utf-8")
        return

    updated = _CLOSURE_DECISION_LINE.sub(r"\1closed", text, count=1)
    updated = _CLOSURE_REASON_LINE.sub(r"\1Closed via grain task close.", updated, count=1)
    updated = _CLOSURE_BLOCKERS_SECTION.sub(r"\1- None\n", updated, count=1)
    results_path.write_text(updated, encoding="utf-8")
