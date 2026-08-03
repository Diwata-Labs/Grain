# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for the Doc Health extension of the generated docs index."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from grain.services.docs_service import generate_index


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _age(path: Path, days: int) -> None:
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
    os.utime(path, (ts, ts))


_FULL_MANIFEST_TAIL = (
    "tasks:\n  root: tasks/\n  packet_files: []\n  patch_dir: patches/\n"
    "  status_values: [done]\n  id_format: x\n"
    "rules:\n  authority_order:\n    - docs/canonical/*\n"
    "  canonical_change_policy: {}\n  context_policy: {}\n"
    "  execution_policy: {}\n  completion_policy: {}\n"
)


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
        "working: []\nruntime: []\n" + _FULL_MANIFEST_TAIL,
    )


def test_index_keeps_existing_sections_and_adds_doc_health(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nLast-verified: 2026-08-01\n\nBody.\n")
    generate_index(tmp_path)
    content = (tmp_path / "docs/runtime/docs_index.md").read_text(encoding="utf-8")

    # existing format is preserved (recognizable to current consumers)
    assert "# Docs Index" in content
    assert "## Authority Order" in content
    assert "## Canonical Docs" in content
    assert "| ID | Path | Authority | Editable by Agents | Purpose |" in content

    # new derived section
    assert "## Doc Health" in content
    assert "2026-08-01" in content


def test_index_health_badges_unverified_canon(tmp_path):
    _manifest(tmp_path)
    doc = tmp_path / "docs/canonical/alpha_spec.md"
    _write(doc, "# Alpha Spec\n\nNo stamp.\n")
    _age(doc, 400)
    generate_index(tmp_path)
    content = (tmp_path / "docs/runtime/docs_index.md").read_text(encoding="utf-8")
    line = next(ln for ln in content.splitlines()
                if "alpha_spec.md" in ln and "## " not in ln and "| highest" not in ln)
    assert "UNVERIFIED" in line


def test_index_health_badges_reference_rot(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nLast-verified: 2099-01-01\n\nSee `scripts/gone.sh`.\n")
    generate_index(tmp_path)
    content = (tmp_path / "docs/runtime/docs_index.md").read_text(encoding="utf-8")
    assert "ROT:1" in content


def test_index_health_lists_unregistered_working_docs(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    _write(tmp_path / "docs/working/floating.md", "# Floating\n")
    generate_index(tmp_path)
    content = (tmp_path / "docs/runtime/docs_index.md").read_text(encoding="utf-8")
    assert "docs/working/floating.md" in content
