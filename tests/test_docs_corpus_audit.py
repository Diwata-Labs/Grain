# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Tests for corpus-level staleness signals in grain docs audit.

Design ruling under test: labels are claims, not truth. Canonical docs can be
stale; a working doc can be more current than the canon it overlaps. No signal
may assume canon=fresh.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from grain.services.docs_audit_service import run_audit


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _age(path: Path, days: int) -> None:
    """Backdate a file's mtime by ``days``."""
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
    os.utime(path, (ts, ts))


def _manifest(tmp_path: Path, extra: str = "") -> None:
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
        "working: []\nruntime: []\n" + extra,
    )


def _findings(result, check_id):
    return [f for f in result.findings if f.check_id == check_id]


def _non_pass(result, check_id):
    return [f for f in _findings(result, check_id) if f.severity != "pass"]


# ── a. reference rot ──────────────────────────────────────────────────────────

def test_reference_rot_flags_missing_cited_path(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nRun `scripts/gone.sh` to deploy.\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    rot = _non_pass(result, "reference_rot")
    assert len(rot) == 1
    assert "scripts/gone.sh" in rot[0].message
    assert "alpha_spec.md" in rot[0].message


def test_reference_rot_applies_to_canonical_docs_too(tmp_path):
    # canon is NOT trusted: a canonical doc with rotten refs is flagged
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nSee [old](../working/deleted.md).\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    assert len(_non_pass(result, "reference_rot")) == 1


def test_reference_rot_passes_when_refs_exist(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "scripts/deploy.sh", "#!/bin/sh\n")
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nRun `scripts/deploy.sh`.\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    assert _non_pass(result, "reference_rot") == []


def test_reference_rot_skips_archive_layer(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    _write(tmp_path / "docs/archive/old_plan.md",
           "# Old Plan\n\nSee `scripts/gone.sh`.\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    assert _non_pass(result, "reference_rot") == []


def test_reference_rot_resolves_against_external_roots(tmp_path):
    # a cross-repo citation like `labs/docs/guide.md` is not rot when the
    # manifest registers an external root named `labs` that contains it
    repo = tmp_path / "repo"
    _write(repo / "docs/runtime/docs_manifest.yaml",
           "version: 2\nproject:\n  name: Test\n"
           "canonical: []\nworking: []\nruntime: []\n"
           "docs_registry:\n  external_roots:\n"
           f"    - name: labs\n      path: {tmp_path / 'labs'}\n")
    _write(tmp_path / "labs/docs/guide.md", "# Guide\n")
    _write(repo / "docs/canonical/spec.md",
           "# Spec\n\nSee `labs/docs/guide.md` and `labs/docs/gone.md`.\n")
    result = run_audit(repo, doc_filter="reference_rot")
    rot = _non_pass(result, "reference_rot")
    assert len(rot) == 1
    assert "labs/docs/gone.md" in rot[0].message
    assert "labs/docs/guide.md" not in rot[0].message


def test_reference_rot_tries_doc_relative_resolution(tmp_path):
    # `canonical/other.md` cited from docs/working/x.md resolves via the doc's
    # parent tree (docs/canonical/other.md) — not rot
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    _write(tmp_path / "docs/working/plan.md",
           "# Plan\n\nSee `canonical/alpha_spec.md`.\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    assert _non_pass(result, "reference_rot") == []


# ── b. subject drift ──────────────────────────────────────────────────────────

def _git(cwd: Path, *args: str, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env)


def test_subject_drift_flags_doc_left_behind(tmp_path):
    _manifest(tmp_path)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")

    _write(tmp_path / "src/mod.py", "x = 0\n")
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nImplemented in `src/mod.py`.\n")
    env = dict(os.environ)
    env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00"
    env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00"
    _git(tmp_path, "add", ".", env=env)
    _git(tmp_path, "commit", "-qm", "init", env=env)

    # the world moved: many commits touch src/mod.py after the doc's last commit
    for i in range(4):
        _write(tmp_path / "src/mod.py", f"x = {i + 1}\n")
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-qm", f"churn {i}")

    _write(
        tmp_path / "docs/runtime/docs_manifest.yaml",
        (tmp_path / "docs/runtime/docs_manifest.yaml").read_text(encoding="utf-8")
        + "audit_thresholds:\n  subject_drift_commits: 3\n",
    )
    result = run_audit(tmp_path, doc_filter="subject_drift")
    drift = _non_pass(result, "subject_drift")
    assert len(drift) == 1
    assert "alpha_spec.md" in drift[0].message
    assert "src/mod.py" in drift[0].message


def test_subject_drift_degrades_gracefully_outside_git(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nSee `src/mod.py`.\n")
    _write(tmp_path / "src/mod.py", "x = 0\n")
    result = run_audit(tmp_path, doc_filter="subject_drift")
    findings = _findings(result, "subject_drift")
    assert findings and all(f.severity == "pass" for f in findings)


# ── c. supersession pressure ──────────────────────────────────────────────────

def test_supersession_emits_promotion_candidate(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    working = tmp_path / "docs/working/alpha_spec_v2.md"
    _write(canon, "# Alpha Spec\n\nOld truth.\n")
    _write(working, "# Alpha Spec v2\n\nNewer truth.\n")
    _write(tmp_path / "docs/working/notes.md",
           "# Notes\n\nSee [v2](alpha_spec_v2.md).\n")
    _age(canon, 200)
    _age(working, 2)

    result = run_audit(tmp_path, doc_filter="supersession")
    cands = _non_pass(result, "supersession")
    assert len(cands) == 1
    msg = cands[0].message
    assert "alpha_spec_v2.md" in msg and "alpha_spec.md" in msg
    assert "may supersede" in msg
    assert "1 inbound ref" in msg
    # it surfaces a queue item, it never auto-rules
    assert "grain docs promote" in cands[0].remediation


def test_supersession_overlap_via_shared_links(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    working = tmp_path / "docs/working/rework_notes.md"
    _write(tmp_path / "src/mod.py", "x = 0\n")
    _write(canon, "# Alpha Spec\n\nCovers `src/mod.py`.\n")
    _write(working, "# Rework Notes\n\nAlso about `src/mod.py`.\n")
    _age(canon, 200)
    _age(working, 2)

    result = run_audit(tmp_path, doc_filter="supersession")
    assert len(_non_pass(result, "supersession")) == 1


def test_supersession_quiet_when_canon_is_newer(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    working = tmp_path / "docs/working/alpha_spec_draft.md"
    _write(canon, "# Alpha Spec\n")
    _write(working, "# Alpha Spec Draft\n")
    _age(canon, 1)
    _age(working, 100)

    result = run_audit(tmp_path, doc_filter="supersession")
    assert _non_pass(result, "supersession") == []


# ── d. verification age ───────────────────────────────────────────────────────

def test_verification_age_nags_unverified_canon(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    _write(canon, "# Alpha Spec\n\nNo stamp.\n")
    _age(canon, 200)
    result = run_audit(tmp_path, doc_filter="verification_age")
    nags = _non_pass(result, "verification_age")
    assert len(nags) == 1
    assert "alpha_spec.md" in nags[0].message
    assert "grain docs verify" in nags[0].remediation


def test_verification_age_old_but_recently_verified_is_fine(tmp_path):
    # old-but-true is fine if recently reread — mtime does NOT drive the nag
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    recent = (datetime.now(tz=timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
    _write(canon, f"# Alpha Spec\n\nLast-verified: {recent}\n\nOld but true.\n")
    _age(canon, 400)
    result = run_audit(tmp_path, doc_filter="verification_age")
    assert _non_pass(result, "verification_age") == []


def test_verification_age_stale_stamp_nags(tmp_path):
    _manifest(tmp_path)
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    _write(canon, "# Alpha Spec\n\nLast-verified: 2025-01-01\n")
    result = run_audit(tmp_path, doc_filter="verification_age")
    assert len(_non_pass(result, "verification_age")) == 1


def test_verification_age_threshold_configurable(tmp_path):
    _manifest(tmp_path, extra="audit_thresholds:\n  canon_unverified_days: 10000\n")
    canon = tmp_path / "docs/canonical/alpha_spec.md"
    _write(canon, "# Alpha Spec\n\nLast-verified: 2025-01-01\n")
    result = run_audit(tmp_path, doc_filter="verification_age")
    assert _non_pass(result, "verification_age") == []


# ── classics ──────────────────────────────────────────────────────────────────

def test_orphan_flags_unlinked_unregistered_doc(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    _write(tmp_path / "docs/working/floating.md", "# Floating Idea\n")
    result = run_audit(tmp_path, doc_filter="orphans")
    orphans = _non_pass(result, "orphans")
    assert len(orphans) == 1
    assert "floating.md" in orphans[0].message


def test_orphan_quiet_when_linked_or_registered(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nSee [notes](../working/floating.md).\n")
    _write(tmp_path / "docs/working/floating.md", "# Floating Idea\n")
    result = run_audit(tmp_path, doc_filter="orphans")
    assert _non_pass(result, "orphans") == []


def test_duplicate_topic_cluster_flagged(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Data Spec\n")
    _write(tmp_path / "docs/working/alpha_data_spec_v2.md", "# Alpha Data Spec v2\n")
    result = run_audit(tmp_path, doc_filter="duplicate_topics")
    dups = _non_pass(result, "duplicate_topics")
    assert len(dups) == 1
    assert "alpha_spec.md" in dups[0].message and "alpha_data_spec_v2.md" in dups[0].message


def test_stale_draft_suggests_archive(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    old = tmp_path / "docs/working/ancient_plan.md"
    _write(old, "# Ancient Plan\n")
    _age(old, 300)
    result = run_audit(tmp_path, doc_filter="stale_drafts")
    stale = _non_pass(result, "stale_drafts")
    assert len(stale) == 1
    assert "ancient_plan.md" in stale[0].message
    assert "grain docs archive" in stale[0].remediation


def test_stale_draft_excludes_workflow_docs(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    bl = tmp_path / "docs/working/backlog.md"
    _write(bl, "# Backlog\n")
    _age(bl, 300)
    result = run_audit(tmp_path, doc_filter="stale_drafts")
    assert _non_pass(result, "stale_drafts") == []


def test_manifest_unregistered_doc_flagged(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    _write(tmp_path / "docs/canonical/mystery.md", "# Mystery\n")
    result = run_audit(tmp_path, doc_filter="manifest_reconciliation")
    unreg = _non_pass(result, "manifest_unregistered")
    assert len(unreg) == 1
    assert "mystery.md" in unreg[0].message


# ── wiring ────────────────────────────────────────────────────────────────────

def test_corpus_filter_runs_all_corpus_signals_only(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    result = run_audit(tmp_path, doc_filter="corpus")
    check_ids = {f.check_id for f in result.findings}
    assert "reference_rot" in check_ids
    assert "verification_age" in check_ids
    # workspace-doc checks are not part of the corpus group
    assert "current_task_stale_pointer" not in check_ids


def test_corpus_findings_group_by_signal(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md",
           "# Alpha Spec\n\nSee `scripts/gone.sh`.\n")
    result = run_audit(tmp_path, doc_filter="reference_rot")
    rot = _non_pass(result, "reference_rot")
    assert rot[0].doc == "reference_rot"


def test_run_audit_reports_progress(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    seen: list[str] = []
    run_audit(tmp_path, doc_filter="corpus", progress=seen.append)
    assert seen  # at least one progress message during corpus scanning


def test_default_audit_includes_corpus_signals(tmp_path):
    _manifest(tmp_path)
    _write(tmp_path / "docs/working/current_task.md",
           "# Current Task\n\nTask ID: none\nTask Path: none\nStatus: unset\n")
    _write(tmp_path / "docs/canonical/alpha_spec.md", "# Alpha Spec\n")
    result = run_audit(tmp_path)
    check_ids = {f.check_id for f in result.findings}
    assert "reference_rot" in check_ids and "current_task_stale_pointer" in check_ids


# ── manifest schema v2 template ───────────────────────────────────────────────

def test_bundled_manifest_template_is_v2_and_valid():
    import yaml
    from pathlib import Path as _P

    import grain
    from grain.validators.manifest_validator import validate_manifest_schema

    template = _P(grain.__file__).parent / "data" / "runtime" / "docs_manifest.yaml"
    manifest = yaml.safe_load(template.read_text(encoding="utf-8"))
    assert manifest["version"] == 2
    assert manifest["docs_registry"]["corpus_dirs"] == [
        "docs/canonical", "docs/working", "docs/archive",
    ]
    assert manifest["docs_registry"]["external_roots"] == []
    assert manifest["audit_thresholds"]["canon_unverified_days"] == 90
    assert manifest["audit_thresholds"]["subject_drift_commits"] == 10
    assert manifest["audit_thresholds"]["draft_archive_days"] == 120
    assert validate_manifest_schema(manifest) == []


def test_v1_manifest_without_new_blocks_still_works(tmp_path):
    # graceful v1 handling: no docs_registry / audit_thresholds anywhere
    _write(tmp_path / "docs/runtime/docs_manifest.yaml",
           "version: 1\nproject:\n  name: Test\ncanonical: []\nworking: []\nruntime: []\n")
    _write(tmp_path / "docs/canonical/spec.md", "# Spec\n\nSee `scripts/gone.sh`.\n")
    result = run_audit(tmp_path, doc_filter="corpus")
    assert any(f.check_id == "reference_rot" and f.severity != "pass"
               for f in result.findings)
