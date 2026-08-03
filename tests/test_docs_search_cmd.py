# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for grain docs search — corpus text search across registry roots."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from grain.cli import main
from grain.services.docs_search_service import search_corpus


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


def _corpus(tmp_path: Path) -> None:
    _write(tmp_path / "docs/runtime/docs_manifest.yaml",
           "version: 2\nproject:\n  name: Test\ncanonical: []\nworking: []\nruntime: []\n")
    _write(tmp_path / "docs/canonical/vault_spec.md",
           "# Vault Spec\n\nAppend-only artifact storage for the bronze layer.\n")
    _write(tmp_path / "docs/working/notes.md",
           "# Notes\n\nRandom notes mentioning vault once.\n")
    _write(tmp_path / "docs/archive/old.md",
           "# Old\n\nNothing relevant.\n")


# ── Service ───────────────────────────────────────────────────────────────────

def test_search_ranks_title_match_above_body_mention(tmp_path):
    _corpus(tmp_path)
    hits = search_corpus(tmp_path, "vault")
    assert len(hits) == 2
    assert hits[0].rel_path == "docs/canonical/vault_spec.md"
    assert hits[1].rel_path == "docs/working/notes.md"
    assert hits[0].score > hits[1].score


def test_search_matches_headings(tmp_path):
    _corpus(tmp_path)
    _write(tmp_path / "docs/working/plan.md",
           "# Plan\n\n## Bronze routing\n\ndetails\n")
    hits = search_corpus(tmp_path, "bronze routing")
    assert hits and hits[0].rel_path == "docs/working/plan.md"


def test_search_no_results(tmp_path):
    _corpus(tmp_path)
    assert search_corpus(tmp_path, "zzzznope") == []


def test_search_spans_external_roots(tmp_path):
    repo = tmp_path / "repo"
    other = tmp_path / "labs" / "docs"
    _corpus(repo)
    _write(other / "grain_guide.md", "# Grain Guide\n\nAll about the vault pattern.\n")
    hits = search_corpus(repo, "vault", extra_roots=[("labs", other)])
    assert any(h.root_name == "labs" and h.rel_path == "grain_guide.md" for h in hits)


def test_search_reads_external_roots_from_manifest(tmp_path):
    repo = tmp_path / "repo"
    other = tmp_path / "labs-docs"
    _corpus(repo)
    _write(other / "guide.md", "# Guide\n\nvault vault vault\n")
    _write(repo / "docs/runtime/docs_manifest.yaml",
           "version: 2\nproject:\n  name: Test\ncanonical: []\nworking: []\nruntime: []\n"
           "docs_registry:\n"
           "  external_roots:\n"
           f"    - name: labs\n      path: {other}\n")
    hits = search_corpus(repo, "vault")
    assert any(h.root_name == "labs" for h in hits)


# ── CLI ───────────────────────────────────────────────────────────────────────

def test_cli_search_text_output(tmp_path):
    _corpus(tmp_path)
    result = _run(tmp_path, "docs", "search", "vault")
    assert result.exit_code == 0
    assert "vault_spec.md" in result.output
    assert "Vault Spec" in result.output


def test_cli_search_json_output(tmp_path):
    _corpus(tmp_path)
    result = _run(tmp_path, "docs", "search", "vault", fmt="json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["query"] == "vault"
    assert data["results"][0]["path"] == "docs/canonical/vault_spec.md"
    assert "score" in data["results"][0]


def test_cli_search_limit(tmp_path):
    _corpus(tmp_path)
    result = _run(tmp_path, "docs", "search", "vault", "--limit", "1", fmt="json")
    data = json.loads(result.output)
    assert len(data["results"]) == 1


def test_cli_search_roots_flag(tmp_path):
    repo = tmp_path / "repo"
    other = tmp_path / "elsewhere"
    _corpus(repo)
    _write(other / "doc.md", "# Elsewhere\n\nvault content\n")
    result = _run(repo, "docs", "search", "vault", "--roots", str(other), fmt="json")
    data = json.loads(result.output)
    assert any(r["root"] == "elsewhere" for r in data["results"])


def test_cli_search_no_results_exits_zero(tmp_path):
    _corpus(tmp_path)
    result = _run(tmp_path, "docs", "search", "zzzznope")
    assert result.exit_code == 0
    assert "no results" in result.output.lower()


def test_cli_search_refreshes_derived_index(tmp_path):
    _corpus(tmp_path)
    index = tmp_path / "docs/runtime/docs_index.md"
    assert not index.exists()
    _run(tmp_path, "docs", "search", "vault")
    assert index.exists()  # registry is derived; commands refresh it before answering


def test_cli_search_no_refresh_skips_index_write(tmp_path):
    _corpus(tmp_path)
    index = tmp_path / "docs/runtime/docs_index.md"
    _run(tmp_path, "docs", "search", "vault", "--no-refresh")
    assert not index.exists()
