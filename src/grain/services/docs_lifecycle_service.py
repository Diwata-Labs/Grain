# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Docs lifecycle mechanics — verify, archive, promote.

These commands handle the FILE/STATUS/INDEX mechanics of the doc lifecycle;
content judgement (what supersedes what, how to merge) stays human/agent work.

Tombstone mechanism: archiving or promoting a doc leaves a small stub at the
old path containing the ``<!-- grain:tombstone -->`` marker and a relative link
to the new location. Chosen over a rewrite-inbound-links pass because inbound
links can live in OTHER repos (the corpus is multi-root); a stub keeps every
inbound link resolving with zero writes outside the doc itself. Audit signals
recognize the marker and treat tombstones as invisible for lifecycle checks;
reference rot still validates the tombstone's forward link.

Manifest edits are surgical: only the entry's ``path:`` line is rewritten via
exact-string replacement, so comments, ordering, and formatting in the
hand-maintained manifest survive. When a surgical edit is not safely possible,
the command emits a warning instead of rewriting the file wholesale.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from grain.domain.command_result import CommandResult

TOMBSTONE_MARKER = "<!-- grain:tombstone -->"

_MANIFEST_REL = "docs/runtime/docs_manifest.yaml"
_ARCHIVE_DIR = "docs/archive"
_CANONICAL_DIR = "docs/canonical"


# ── Doc resolution ────────────────────────────────────────────────────────────

def _manifest_entries(root: Path) -> list[dict]:
    manifest_path = root / _MANIFEST_REL
    if not manifest_path.exists():
        return []
    try:
        import yaml  # type: ignore

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    entries: list[dict] = []
    for layer in ("canonical", "working", "runtime"):
        for entry in manifest.get(layer) or []:
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def resolve_doc(root: Path, doc: str) -> Path | None:
    """Resolve a doc argument (repo-relative path or manifest id) to a file."""
    candidate = root / doc
    if candidate.is_file():
        return candidate
    for entry in _manifest_entries(root):
        if entry.get("id") == doc:
            path = root / str(entry.get("path", ""))
            if path.is_file():
                return path
    return None


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_tombstone_text(text: str) -> bool:
    return TOMBSTONE_MARKER in text


# ── verify ────────────────────────────────────────────────────────────────────

def verify_doc(root: Path, doc: str, when: date | None = None) -> CommandResult:
    """Bump the doc's Last-verified stamp (distinct from last-modified)."""
    from grain.services.docs_corpus import set_verified_stamp
    from grain.services.docs_service import refresh_index

    path = resolve_doc(root, doc)
    if path is None:
        return CommandResult(
            ok=False, command="docs verify", repo=str(root),
            errors=[f"doc not found: {doc} (path or manifest id)"],
        )

    text = path.read_text(encoding="utf-8")
    path.write_text(set_verified_stamp(text, when or date.today()), encoding="utf-8")

    result = CommandResult(
        ok=True, command="docs verify", repo=str(root),
        files_updated=[_rel(root, path)],
    )
    if refresh_index(root):
        result.files_updated.append("docs/runtime/docs_index.md")
    return result


# ── archive ───────────────────────────────────────────────────────────────────

def _tombstone_text(title: str, new_rel: str, link: str, verb: str) -> str:
    today = date.today().isoformat()
    label = f"# {title} (archived)\n" if verb == "archived" else f"# {title} (promoted)\n"
    return (
        f"{label}"
        f"{TOMBSTONE_MARKER}\n\n"
        f"> **{verb.upper()}** — moved to [{new_rel}]({link}) on {today} "
        f"by `grain docs {'archive' if verb == 'archived' else 'promote'}`.\n"
    )


def _link_from(src: Path, dest: Path) -> str:
    return Path(os.path.relpath(dest, src.parent)).as_posix()


def _rewrite_manifest_path(root: Path, old_rel: str, new_rel: str) -> tuple[bool, str]:
    """Surgically rewrite a single ``path: <old>`` line in the manifest.

    Returns (rewritten, warning). Never rewrites unless the target line is
    unambiguous; never round-trips the YAML (comments survive).
    """
    manifest_path = root / _MANIFEST_REL
    if not manifest_path.exists():
        return False, ""
    text = manifest_path.read_text(encoding="utf-8")
    if f"path: {old_rel}" not in text:
        return False, ""  # doc was not registered — nothing to do
    if text.count(f"path: {old_rel}") > 1:
        return False, (
            f"manifest lists 'path: {old_rel}' more than once — "
            f"update it manually to {new_rel}"
        )
    if f"path: {new_rel}" in text:
        return False, (
            f"manifest already has an entry for {new_rel}; the entry pointing at "
            f"{old_rel} now targets a tombstone — remove or repoint it manually"
        )
    manifest_path.write_text(
        text.replace(f"path: {old_rel}", f"path: {new_rel}", 1), encoding="utf-8"
    )
    return True, ""


def archive_doc(root: Path, doc: str) -> CommandResult:
    """Move a doc to docs/archive/ leaving a tombstone stub at the old path."""
    from grain.services.docs_service import refresh_index

    cmd = "docs archive"
    src = resolve_doc(root, doc)
    if src is None:
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"doc not found: {doc} (path or manifest id)"])

    src_rel = _rel(root, src)
    if src_rel.startswith(_ARCHIVE_DIR + "/"):
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"{src_rel} is already in {_ARCHIVE_DIR}/"])
    text = src.read_text(encoding="utf-8")
    if is_tombstone_text(text):
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"{src_rel} is a tombstone — nothing to archive"])

    dest = root / _ARCHIVE_DIR / src.name
    dest_rel = _rel(root, dest) if dest.exists() else f"{_ARCHIVE_DIR}/{src.name}"
    if dest.exists():
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"{dest_rel} already exists — rename first"])

    from grain.services.docs_corpus import extract_title

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    title = extract_title(text) or src.stem
    src.write_text(
        _tombstone_text(title, dest_rel, _link_from(src, dest), "archived"),
        encoding="utf-8",
    )

    result = CommandResult(
        ok=True, command=cmd, repo=str(root),
        files_created=[dest_rel],
        files_updated=[src_rel],
    )
    rewritten, warning = _rewrite_manifest_path(root, src_rel, dest_rel)
    if rewritten:
        result.files_updated.append(_MANIFEST_REL)
    if warning:
        result.warnings.append(warning)
    if refresh_index(root):
        result.files_updated.append("docs/runtime/docs_index.md")
    return result


# ── promote ───────────────────────────────────────────────────────────────────

def promote_doc(root: Path, doc: str, into: str) -> CommandResult:
    """Promote a working doc into canonical — the supersession queue's resolution.

    Mechanics only (content merging stays human/agent work):
    * ``into="new"`` — move the doc to docs/canonical/<name>, stamp Last-verified.
    * ``into=<canon>`` — archive the superseded canon (with a supersession note),
      install the working doc's content at the canon path, stamp Last-verified.
    Either way the old working path becomes a tombstone.
    """
    from grain.services.docs_corpus import extract_title, set_verified_stamp
    from grain.services.docs_service import refresh_index

    cmd = "docs promote"
    src = resolve_doc(root, doc)
    if src is None:
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"doc not found: {doc} (path or manifest id)"])
    src_rel = _rel(root, src)
    text = src.read_text(encoding="utf-8")
    if is_tombstone_text(text):
        return CommandResult(ok=False, command=cmd, repo=str(root),
                             errors=[f"{src_rel} is a tombstone — nothing to promote"])

    today = date.today()
    result = CommandResult(ok=True, command=cmd, repo=str(root))

    if into == "new":
        dest = root / _CANONICAL_DIR / src.name
        dest_rel = f"{_CANONICAL_DIR}/{src.name}"
        if dest.exists():
            return CommandResult(
                ok=False, command=cmd, repo=str(root),
                errors=[f"{dest_rel} already exists — use --into {dest_rel} to supersede it"],
            )
    else:
        target = resolve_doc(root, into)
        if target is None:
            return CommandResult(ok=False, command=cmd, repo=str(root),
                                 errors=[f"promotion target not found: {into}"])
        dest = target
        dest_rel = _rel(root, dest)
        if not dest_rel.startswith(_CANONICAL_DIR + "/"):
            return CommandResult(ok=False, command=cmd, repo=str(root),
                                 errors=[f"promotion target must be canonical: {dest_rel}"])

        # archive the superseded canon with a supersession note
        archived = root / _ARCHIVE_DIR / dest.name
        archived_rel = f"{_ARCHIVE_DIR}/{dest.name}"
        if archived.exists():
            return CommandResult(ok=False, command=cmd, repo=str(root),
                                 errors=[f"{archived_rel} already exists — rename first"])
        old_text = dest.read_text(encoding="utf-8")
        note = (
            f"\n> Superseded by [{dest_rel}]({_link_from(archived, dest)}) "
            f"(content promoted from {src_rel}) on {today.isoformat()}.\n"
        )
        archived.parent.mkdir(parents=True, exist_ok=True)
        archived.write_text(_insert_after_title(old_text, note), encoding="utf-8")
        result.files_created.append(archived_rel)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(set_verified_stamp(text, today), encoding="utf-8")
    if into == "new":
        result.files_created.append(dest_rel)
    else:
        result.files_updated.append(dest_rel)

    title = extract_title(text) or src.stem
    src.write_text(
        _tombstone_text(title, dest_rel, _link_from(src, dest), "promoted"),
        encoding="utf-8",
    )
    result.files_updated.append(src_rel)

    rewritten, warning = _rewrite_manifest_path(root, src_rel, dest_rel)
    if rewritten:
        result.files_updated.append(_MANIFEST_REL)
    if warning:
        result.warnings.append(warning)
    if refresh_index(root):
        result.files_updated.append("docs/runtime/docs_index.md")
    return result


def _insert_after_title(text: str, insert: str) -> str:
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, insert)
            return "".join(lines)
    return insert.lstrip("\n") + text
