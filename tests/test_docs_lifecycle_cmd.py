# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for grain docs verify / archive / promote — doc lifecycle mechanics."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from click.testing import CliRunner

from grain.cli import main
from grain.services.docs_corpus import read_verified_stamp
from grain.services.docs_lifecycle_service import archive_doc, promote_doc, verify_doc


def _run(tmp_path: Path, *args: str, fmt: str = "text"):
    runner = CliRunner()
    cmd = ["--repo", str(tmp_path)]
    if fmt == "json":
        cmd += ["--format", "json"]
    cmd += list(args)
    return runner.invoke(main, cmd)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/runtime/docs_manifest.yaml",
        "version: 2\nproject:\n  name: Test\n"
        "canonical:\n"
        "  - id: alpha_spec\n"
        "    path: docs/canonical/alpha_spec.md\n"
        "    purpose: Alpha spec\n"
        "    authority: highest\n"
        "    editable_by_agents: false\n"
        "    read_when: [always]\n"
        "working:\n"
        "  - id: beta_notes\n"
        "    path: docs/working/beta_notes.md\n"
        "    purpose: Beta notes\n"
        "    authority: informational\n"
        "    editable_by_agents: true\n"
        "    read_when: [always]\n"
        "runtime: []\n",
    )


# ── verify ────────────────────────────────────────────────────────────────────

def test_verify_stamps_doc_by_path(tmp_path):
    _manifest(tmp_path)
    doc = tmp_path / "docs/canonical/alpha_spec.md"
    _write(doc, "# Alpha Spec\n\nBody.\n")
    result = verify_doc(tmp_path, "docs/canonical/alpha_spec.md")
    assert result.ok
    assert read_verified_stamp(doc.read_text(encoding="utf-8")) == date.today()


def test_verify_resolves_manifest_id(tmp_path):
    _manifest(tmp_path)
    doc = tmp_path / "docs/canonical/alpha_spec.md"
    _write(doc, "# Alpha Spec\n")
    result = verify_doc(tmp_path, "alpha_spec")
    assert result.ok
    assert read_verified_stamp(doc.read_text(encoding="utf-8")) == date.today()


def test_verify_missing_doc_fails(tmp_path):
    _manifest(tmp_path)
    result = verify_doc(tmp_path, "docs/canonical/nope.md")
    assert not result.ok


def test_cli_verify(tmp_path):
    _manifest(tmp_path)
    doc = tmp_path / "docs/canonical/alpha_spec.md"
    _write(doc, "# Alpha Spec\n")
    result = _run(tmp_path, "docs", "verify", "alpha_spec")
    assert result.exit_code == 0
    assert "Last-verified" in doc.read_text(encoding="utf-8")


# ── archive ───────────────────────────────────────────────────────────────────

def test_archive_moves_doc_and_leaves_tombstone(tmp_path):
    _manifest(tmp_path)
    src = tmp_path / "docs/working/beta_notes.md"
    _write(src, "# Beta Notes\n\nContent worth keeping.\n")
    result = archive_doc(tmp_path, "docs/working/beta_notes.md")
    assert result.ok

    dest = tmp_path / "docs/archive/beta_notes.md"
    assert dest.exists()
    assert "Content worth keeping." in dest.read_text(encoding="utf-8")

    # tombstone: stub at old path keeps inbound links from rotting
    stub = src.read_text(encoding="utf-8")
    assert "grain:tombstone" in stub
    assert "../archive/beta_notes.md" in stub


def test_archive_updates_manifest_path_surgically(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    archive_doc(tmp_path, "beta_notes")
    manifest_text = (tmp_path / "docs/runtime/docs_manifest.yaml").read_text(encoding="utf-8")
    assert "path: docs/archive/beta_notes.md" in manifest_text
    assert "path: docs/working/beta_notes.md" not in manifest_text
    # surgical: untouched lines survive (comments/other entries intact)
    assert "id: alpha_spec" in manifest_text


def test_archive_refreshes_index(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    archive_doc(tmp_path, "beta_notes")
    index = tmp_path / "docs/runtime/docs_index.md"
    assert index.exists()
    assert "docs/archive/beta_notes.md" in index.read_text(encoding="utf-8")


def test_archive_refuses_existing_dest(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    _write(tmp_path / "docs/archive/beta_notes.md", "# Old one\n")
    result = archive_doc(tmp_path, "beta_notes")
    assert not result.ok


def test_archived_tombstone_is_invisible_to_audit(tmp_path):
    from grain.services.docs_audit_service import run_audit

    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    archive_doc(tmp_path, "beta_notes")
    result = run_audit(tmp_path, doc_filter="corpus")
    non_pass = [f for f in result.findings if f.severity != "pass"]
    assert all("beta_notes" not in f.message or "archive" in f.message.lower()
               for f in non_pass), [f.message for f in non_pass]
    # specifically: the tombstone is neither an orphan nor unregistered
    assert not [f for f in non_pass if f.check_id in ("orphans", "manifest_unregistered")]


def test_cli_archive(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    result = _run(tmp_path, "docs", "archive", "beta_notes")
    assert result.exit_code == 0
    assert (tmp_path / "docs/archive/beta_notes.md").exists()


# ── promote ───────────────────────────────────────────────────────────────────

def test_promote_into_new_canonical(tmp_path):
    _manifest(tmp_path)
    src = tmp_path / "docs/working/beta_notes.md"
    _write(src, "# Beta Notes\n\nThe real state of things.\n")
    result = promote_doc(tmp_path, "docs/working/beta_notes.md", into="new")
    assert result.ok

    dest = tmp_path / "docs/canonical/beta_notes.md"
    text = dest.read_text(encoding="utf-8")
    assert "The real state of things." in text
    assert read_verified_stamp(text) == date.today()  # promotion stamps Last-verified
    assert "grain:tombstone" in src.read_text(encoding="utf-8")


def test_promote_into_existing_canon_archives_superseded(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    working = tmp_path / "docs/working/beta_notes.md"
    _write(canon, "# Alpha Spec\n\nOld truth.\n")
    _write(working, "# Alpha Spec v2\n\nNew truth.\n")

    result = promote_doc(tmp_path, "docs/working/beta_notes.md",
                         into="docs/canonical/alpha_spec.md")
    assert result.ok

    # the canon path now carries the promoted content, stamped
    text = canon.read_text(encoding="utf-8")
    assert "New truth." in text
    assert read_verified_stamp(text) == date.today()

    # the superseded canon is preserved in archive/ with a supersession note
    archived = (tmp_path / "docs/archive/alpha_spec.md").read_text(encoding="utf-8")
    assert "Old truth." in archived
    assert "Superseded" in archived

    # tombstone at the working doc's old path
    assert "grain:tombstone" in working.read_text(encoding="utf-8")


def test_promote_missing_target_fails(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n")
    result = promote_doc(tmp_path, "docs/working/beta_notes.md",
                         into="docs/canonical/nope.md")
    assert not result.ok


def test_cli_promote_json(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/beta_notes.md", "# Beta Notes\n\nBody.\n")
    result = _run(tmp_path, "docs", "promote", "beta_notes", "--into", "new", fmt="json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
