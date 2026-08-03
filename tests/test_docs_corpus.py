# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for the shared docs corpus model (grain.services.docs_corpus)."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from grain.services.docs_corpus import (
    extract_headings,
    extract_links,
    extract_path_refs,
    extract_title,
    git_churn_since,
    git_last_commit_date,
    load_corpus,
    read_verified_stamp,
    set_verified_stamp,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── Extraction helpers ────────────────────────────────────────────────────────

def test_extract_title_uses_first_h1():
    assert extract_title("# Vault Spec\n\nBody\n") == "Vault Spec"


def test_extract_title_falls_back_to_empty():
    assert extract_title("no heading here\n") == ""


def test_extract_headings_collects_all_levels():
    text = "# Title\n\n## Section A\n\ncontent\n\n### Sub B\n"
    assert extract_headings(text) == ["Title", "Section A", "Sub B"]


def test_extract_links_returns_markdown_link_targets():
    text = "See [the spec](../canonical/vault_spec.md) and [ext](https://x.y/z).\n"
    links = extract_links(text)
    assert "../canonical/vault_spec.md" in links
    # external URLs are not corpus links
    assert all(not link.startswith("http") for link in links)


def test_extract_path_refs_finds_code_span_paths():
    text = "Run `scripts/deploy.sh` after editing `src/grain/cli/docs.py`.\n"
    refs = extract_path_refs(text)
    assert "scripts/deploy.sh" in refs
    assert "src/grain/cli/docs.py" in refs


def test_extract_path_refs_ignores_non_paths():
    text = "Use `--format json` with `grain docs audit` and `version: 2`.\n"
    assert extract_path_refs(text) == []


def test_extract_path_refs_ignores_urls_and_globs():
    text = "See `https://example.com/a.md` and `docs/canonical/*` patterns.\n"
    refs = extract_path_refs(text)
    assert refs == []


# ── Verification stamps ───────────────────────────────────────────────────────

def test_read_verified_stamp_header_line():
    text = "# Spec\n\nLast-verified: 2026-07-01\n\nBody\n"
    assert read_verified_stamp(text) == date(2026, 7, 1)


def test_read_verified_stamp_frontmatter():
    text = "---\ntitle: Spec\nverified: 2026-06-15\n---\n\n# Spec\n"
    assert read_verified_stamp(text) == date(2026, 6, 15)


def test_read_verified_stamp_absent():
    assert read_verified_stamp("# Spec\n\nBody\n") is None


def test_set_verified_stamp_inserts_after_title():
    text = "# Spec\n\nBody\n"
    out = set_verified_stamp(text, date(2026, 8, 3))
    assert read_verified_stamp(out) == date(2026, 8, 3)
    lines = out.splitlines()
    assert lines[0] == "# Spec"
    assert "Body" in out


def test_set_verified_stamp_updates_existing():
    text = "# Spec\n\nLast-verified: 2026-01-01\n\nBody\n"
    out = set_verified_stamp(text, date(2026, 8, 3))
    assert out.count("Last-verified:") == 1
    assert read_verified_stamp(out) == date(2026, 8, 3)


def test_set_verified_stamp_updates_frontmatter():
    text = "---\ntitle: Spec\nverified: 2026-01-01\n---\n\n# Spec\n"
    out = set_verified_stamp(text, date(2026, 8, 3))
    assert read_verified_stamp(out) == date(2026, 8, 3)
    assert out.startswith("---\n")


# ── Corpus loading ────────────────────────────────────────────────────────────

def test_load_corpus_scans_default_dirs(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n\nsee [w](../working/notes.md)\n")
    _write(tmp_path / "docs/working/notes.md", "# Notes\n")
    _write(tmp_path / "docs/archive/old.md", "# Old\n")
    _write(tmp_path / "docs/runtime/docs_index.md", "# Docs Index\n")
    _write(tmp_path / "README.md", "# Readme\n")

    corpus = load_corpus(tmp_path)
    rels = {d.rel_path for d in corpus}
    assert rels == {"docs/canonical/spec.md", "docs/working/notes.md", "docs/archive/old.md"}
    layers = {d.rel_path: d.layer for d in corpus}
    assert layers["docs/canonical/spec.md"] == "canonical"
    assert layers["docs/working/notes.md"] == "working"
    assert layers["docs/archive/old.md"] == "archive"


def test_load_corpus_resolves_links_relative_to_doc(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "see [w](../working/notes.md)\n")
    _write(tmp_path / "docs/working/notes.md", "# Notes\n")
    corpus = load_corpus(tmp_path)
    spec = next(d for d in corpus if d.rel_path == "docs/canonical/spec.md")
    assert "docs/working/notes.md" in spec.resolved_links


def test_load_corpus_external_roots(tmp_path):
    repo = tmp_path / "repo"
    other = tmp_path / "other-repo" / "docs"
    _write(repo / "docs/canonical/spec.md", "# Spec\n")
    _write(other / "guide.md", "# Guide\n")

    corpus = load_corpus(repo, external_roots=[("other", other)])
    names = {(d.root_name, d.rel_path) for d in corpus}
    assert ("", "docs/canonical/spec.md") in names
    assert ("other", "guide.md") in names


def test_load_corpus_missing_external_root_is_skipped(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n")
    corpus = load_corpus(tmp_path, external_roots=[("gone", tmp_path / "nope")])
    assert {d.rel_path for d in corpus} == {"docs/canonical/spec.md"}


# ── Extraction cache (incremental refresh) ────────────────────────────────────

def test_load_corpus_writes_extraction_cache(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n")
    load_corpus(tmp_path, use_cache=True)
    assert (tmp_path / ".grain" / "docs_corpus_cache.json").exists()


def test_load_corpus_cache_reparses_only_changed_files(tmp_path, monkeypatch):
    import grain.services.docs_corpus as dc

    _write(tmp_path / "docs/canonical/a.md", "# A\n")
    _write(tmp_path / "docs/canonical/b.md", "# B\n")
    load_corpus(tmp_path, use_cache=True)  # cold: parses both, writes cache

    calls: list[str] = []
    real = dc._parse_doc

    def spy(path, root, root_name):
        calls.append(path.name)
        return real(path, root, root_name)

    monkeypatch.setattr(dc, "_parse_doc", spy)

    # warm load with no changes → nothing re-parsed
    corpus = load_corpus(tmp_path, use_cache=True)
    assert calls == []
    assert {d.title for d in corpus} == {"A", "B"}

    # change one file (content + newer mtime) → only that file re-parsed
    import os
    a = tmp_path / "docs/canonical/a.md"
    a.write_text("# A2\n", encoding="utf-8")
    os.utime(a, (a.stat().st_atime + 5, a.stat().st_mtime + 5))
    corpus = load_corpus(tmp_path, use_cache=True)
    assert calls == ["a.md"]
    assert {d.title for d in corpus} == {"A2", "B"}


def test_load_corpus_cache_detects_new_and_deleted_files(tmp_path):
    _write(tmp_path / "docs/canonical/a.md", "# A\n")
    load_corpus(tmp_path, use_cache=True)

    _write(tmp_path / "docs/canonical/new.md", "# New\n")
    (tmp_path / "docs/canonical/a.md").unlink()
    corpus = load_corpus(tmp_path, use_cache=True)
    assert {d.rel_path for d in corpus} == {"docs/canonical/new.md"}


def test_corpus_doc_body_reads_lazily(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n\nbody words here\n")
    load_corpus(tmp_path, use_cache=True)
    corpus = load_corpus(tmp_path, use_cache=True)  # from cache — no text parsed
    doc = corpus[0]
    assert "body words here" in doc.body()


# ── Git helpers (graceful degradation) ────────────────────────────────────────

def test_git_helpers_degrade_outside_repo(tmp_path):
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n")
    assert git_last_commit_date(tmp_path, "docs/canonical/spec.md") is None
    assert git_churn_since(tmp_path, ["src/"], "2026-01-01") is None


def test_git_commit_index_batches_history(tmp_path):
    from grain.services.docs_corpus import load_git_commit_index, last_commit_dates

    assert load_git_commit_index(tmp_path) is None  # graceful outside git

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    _write(tmp_path / "doc.md", "# Doc\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "one"], cwd=tmp_path, check=True)
    _write(tmp_path / "src.py", "x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "two"], cwd=tmp_path, check=True)

    index = load_git_commit_index(tmp_path)
    assert index is not None and len(index) == 2
    dates = last_commit_dates(index)
    assert "doc.md" in dates and "src.py" in dates
    # churn derivable from the one batched walk: commits touching src.py
    touching = [c for c in index if "src.py" in c[1]]
    assert len(touching) == 1


def test_git_helpers_inside_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    _write(tmp_path / "doc.md", "# Doc\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "one"], cwd=tmp_path, check=True)

    assert git_last_commit_date(tmp_path, "doc.md") is not None

    _write(tmp_path / "src.py", "x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "two"], cwd=tmp_path, check=True)

    churn = git_churn_since(tmp_path, ["src.py"], "2000-01-01")
    assert churn is not None and churn >= 1
