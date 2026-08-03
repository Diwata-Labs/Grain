# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for grain docs audit CLI flags: exit semantics, --strict, --no-refresh."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from grain.cli import main


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


def _workspace(tmp_path: Path) -> None:
    _write(tmp_path / "docs/runtime/docs_manifest.yaml",
           "version: 2\nproject:\n  name: Test\ncanonical: []\nworking: []\nruntime: []\n")
    _write(tmp_path / "docs/working/current_task.md",
           "# Current Task\n\nTask ID: none\nTask Path: none\nStatus: unset\n")
    _write(tmp_path / "docs/working/backlog.md",
           "# Backlog\n\n## 2. Phase 1 — Foundation\n\n### P1-T01 — A task\n- **Status:** done\n")
    _write(tmp_path / "docs/working/current_focus.md",
           "# Current Focus\n\n## Current Phase\nPhase 1 — Foundation\n")


def test_audit_with_findings_still_exits_zero_by_default(tmp_path):
    # non-empty audit must NOT exit non-zero without --strict
    _workspace(tmp_path)
    _write(tmp_path / "docs/canonical/rotten.md",
           "# Rotten\n\nSee `scripts/gone.sh`.\n")
    result = _run(tmp_path, "docs", "audit", "--doc", "reference_rot")
    assert result.exit_code == 0
    assert "reference_rot" in result.output


def test_audit_strict_exits_nonzero_on_findings(tmp_path):
    _workspace(tmp_path)
    _write(tmp_path / "docs/canonical/rotten.md",
           "# Rotten\n\nSee `scripts/gone.sh`.\n")
    result = _run(tmp_path, "docs", "audit", "--doc", "reference_rot", "--strict")
    assert result.exit_code != 0


def test_audit_strict_exits_zero_when_clean(tmp_path):
    _workspace(tmp_path)
    result = _run(tmp_path, "docs", "audit", "--doc", "reference_rot", "--strict")
    assert result.exit_code == 0


def test_audit_json_is_parseable_with_corpus_signals(tmp_path):
    _workspace(tmp_path)
    _write(tmp_path / "docs/canonical/rotten.md",
           "# Rotten\n\nSee `scripts/gone.sh`.\n")
    result = _run(tmp_path, "docs", "audit", fmt="json")
    data = json.loads(result.output)
    assert any(f["check_id"] == "reference_rot" for f in data["findings"])


def test_audit_refreshes_derived_index_by_default(tmp_path):
    _workspace(tmp_path)
    index = tmp_path / "docs/runtime/docs_index.md"
    assert not index.exists()
    _run(tmp_path, "docs", "audit", "--doc", "reference_rot")
    assert index.exists()


def test_audit_no_refresh_skips_index_write(tmp_path):
    _workspace(tmp_path)
    index = tmp_path / "docs/runtime/docs_index.md"
    _run(tmp_path, "docs", "audit", "--doc", "reference_rot", "--no-refresh")
    assert not index.exists()
