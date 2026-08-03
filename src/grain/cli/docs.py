# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

import json

import click

from grain.adapters.filesystem import resolve_repo_root
from grain.cli.output import print_result
from grain.domain.errors import ValidationError
from grain.services import docs_service


@click.group("docs")
def docs_group():
    """Inspect, search, audit, and manage repository documentation lifecycle.

    \b
    The docs index (docs/runtime/docs_index.md) is DERIVED, never authored:
    every docs command refreshes it incrementally before answering (pass
    --no-refresh where offered to skip). On-demand refresh is the default
    trigger. Recommended integrations (not installed automatically):
      git hook:  echo 'grain docs index >/dev/null || true' >> .git/hooks/post-commit
      CI:        run `grain docs audit --format json` on a schedule
    """


@docs_group.command("audit")
@click.option("--doc", default=None, help="Run checks only for this group: a working doc (current_task, backlog), "
              "'corpus' for all staleness signals, or one signal (reference_rot, subject_drift, "
              "supersession, verification_age, orphans, duplicate_topics, stale_drafts, manifest_reconciliation).")
@click.option("--severity", default=None, type=click.Choice(["high", "medium"]), help="Filter by minimum severity (high=errors only, medium=warnings+errors).")
@click.option("--fix", is_flag=True, default=False, help="Apply safe auto-fixes (prompts per finding).")
@click.option("--no-confirm", is_flag=True, default=False, help="Apply fixes without prompting (agent use only). Requires --fix.")
@click.option("--strict", is_flag=True, default=False,
              help="Exit non-zero when the audit has findings (CI use). Default: report and exit 0.")
@click.option("--no-refresh", is_flag=True, default=False,
              help="Skip the derived-index refresh before auditing (scripted use).")
@click.pass_context
def docs_audit(ctx, doc, severity, fix, no_confirm, strict, no_refresh):
    """Audit workspace docs AND the docs corpus for staleness.

    Corpus signals treat labels as claims, not truth: reference rot and subject
    drift apply to canonical docs too, verification age nags long-UNVERIFIED
    canon (not long-unedited), and supersession surfaces working docs that may
    be more current than the canon they overlap — as a queue, never auto-ruled.

    \b
    Examples:
      grain docs audit
      grain docs audit --doc corpus
      grain docs audit --doc supersession
      grain docs audit --severity high
      grain docs audit --format json
      grain docs audit --strict   (CI: non-zero exit on findings)
    """
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    if not no_refresh:
        docs_service.refresh_index(root)

    from grain.services.docs_audit_service import run_audit, save_audit_cache, apply_fixes

    # Progress lines go to stderr (text mode only) so long git-backed phases
    # never look like a hang and JSON stdout stays parseable.
    progress = (lambda msg: click.echo(f"  … {msg}", err=True)) if fmt == "text" else None

    result = run_audit(root, doc_filter=doc, severity_filter=severity, progress=progress)
    save_audit_cache(root, result)

    if fmt == "json":
        click.echo(json.dumps({
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
        }, indent=2))
        _maybe_strict_exit(result, strict)
        return

    # --- text output ---
    run_date = result.run_at[:10]
    click.echo(f"grain docs audit — {run_date}")
    click.echo("")

    # Group by doc
    docs_seen: list[str] = []
    findings_by_doc: dict[str, list] = {}
    for f in result.findings:
        if f.doc not in findings_by_doc:
            docs_seen.append(f.doc)
            findings_by_doc[f.doc] = []
        findings_by_doc[f.doc].append(f)

    for doc_key in docs_seen:
        doc_findings = findings_by_doc[doc_key]
        click.echo(doc_key)
        for f in doc_findings:
            if f.severity == "pass":
                symbol = click.style("  ✓", fg="green") if _color_ok() else "  ✓"
                click.echo(f"{symbol}  {f.check_id:<40} {f.message}")
            elif f.severity == "warning":
                symbol = click.style("  ⚠", fg="yellow") if _color_ok() else "  ⚠"
                click.echo(f"{symbol}  {f.check_id:<40} {f.message}")
                if f.remediation:
                    click.echo(f"     → {f.remediation}")
            elif f.severity == "error":
                symbol = click.style("  ✗", fg="red") if _color_ok() else "  ✗"
                click.echo(f"{symbol}  {f.check_id:<40} {f.message}")
                if f.remediation:
                    click.echo(f"     → {f.remediation}")
        click.echo("")

    s = result.summary
    status_color = {"ok": "green", "warning": "yellow", "error": "red"}.get(result.overall, "white")
    status_label = click.style(result.overall, fg=status_color) if _color_ok() else result.overall
    click.echo(
        f"Checks: {s['pass']} pass, {s['warning']} warning(s), {s['error']} error(s) — {status_label}"
    )

    if fix:
        non_pass = [f for f in result.findings if f.severity != "pass"]
        if non_pass:
            applied = apply_fixes(root, result, confirm=not no_confirm)
            if applied:
                click.echo("\nFixes applied:")
                for desc in applied:
                    click.echo(f"  - {desc}")
            else:
                click.echo("\nNo fixes applied.")

    _maybe_strict_exit(result, strict)


def _maybe_strict_exit(result, strict: bool) -> None:
    """--strict: non-zero exit ONLY when asked. A merely non-empty audit must
    never fail scripts by default (the guard-exits-1-on-clean-repos lesson)."""
    if not strict:
        return
    s = result.summary
    if s.get("warning", 0) or s.get("error", 0):
        raise ValidationError(
            "docs audit found issues (--strict)",
            detail=f"{s.get('error', 0)} error(s), {s.get('warning', 0)} warning(s)",
        )


def _color_ok() -> bool:
    ctx = click.get_current_context(silent=True)
    return ctx is not None


@docs_group.command("search")
@click.argument("query")
@click.option(
    "--roots", "roots", multiple=True, type=click.Path(),
    help="Extra external documentation roots to search (repeatable). "
         "Persistent roots belong in docs_registry.external_roots in the manifest.",
)
@click.option("--limit", default=10, show_default=True, help="Maximum results.")
@click.option(
    "--no-refresh", is_flag=True, default=False,
    help="Skip the derived-index refresh before answering (scripted use).",
)
@click.pass_context
def docs_search(ctx, query, roots, limit, no_refresh):
    """Search titles, headings, and bodies across the registry corpus.

    \b
    Examples:
      grain docs search "bronze routing"
      grain docs search vault --limit 5 --format json
      grain docs search vault --roots ~/Diwata/Diwata-Labs/docs
    """
    from pathlib import Path as _Path

    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    if not no_refresh:
        docs_service.refresh_index(root)

    from grain.services.docs_search_service import search_corpus

    extra = [(str(_Path(r).name), _Path(r)) for r in roots]
    hits = search_corpus(root, query, extra_roots=extra, limit=limit)

    if fmt == "json":
        click.echo(json.dumps({
            "query": query,
            "results": [
                {
                    "path": h.rel_path,
                    "root": h.root_name or "",
                    "title": h.title,
                    "score": h.score,
                    "snippet": h.snippet,
                }
                for h in hits
            ],
        }, indent=2))
        return

    if not hits:
        click.echo(f"grain docs search — no results for '{query}'")
        return

    click.echo(f"grain docs search — {len(hits)} result(s) for '{query}'")
    click.echo("")
    for i, h in enumerate(hits, 1):
        loc = f"{h.root_name}:{h.rel_path}" if h.root_name else h.rel_path
        title = f" — {h.title}" if h.title else ""
        click.echo(f"  {i}. {loc}{title}  (score {h.score})")
        if h.snippet:
            click.echo(f"     {h.snippet}")


@docs_group.command("validate")
@click.pass_context
def docs_validate(ctx):
    """Validate required documentation structure and contracts."""
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    result = docs_service.validate_docs(root)
    print_result(result, fmt=fmt)

    if not result.ok:
        raise ValidationError("docs validation failed", detail=f"{len(result.errors)} error(s)")


@docs_group.command("index")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Print intended output without writing files.",
)
@click.pass_context
def docs_index(ctx, dry_run):
    """Generate or refresh docs/runtime/docs_index.md from the manifest."""
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    result = docs_service.generate_index(root, dry_run=dry_run)
    print_result(result, fmt=fmt)

    if not result.ok:
        raise ValidationError("docs index generation failed")


@docs_group.command("verify")
@click.argument("doc")
@click.option("--date", "when", default=None, help="Stamp date (YYYY-MM-DD, default today).")
@click.pass_context
def docs_verify(ctx, doc, when):
    """Bump a doc's Last-verified stamp — 'I reread this; it is still true.'

    Verification age is distinct from last-modified: canon staleness means
    long-UNVERIFIED, not long-unedited. `grain docs audit` nags canonical docs
    whose stamp (or, unstamped, whose last edit) is older than the manifest's
    audit_thresholds.canon_unverified_days.

    \b
    Examples:
      grain docs verify docs/canonical/architecture.md
      grain docs verify architecture --date 2026-08-01
    """
    from datetime import date as _date

    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    parsed = None
    if when:
        try:
            parsed = _date.fromisoformat(when)
        except ValueError:
            raise click.UsageError(f"--date must be YYYY-MM-DD, got {when!r}")

    from grain.services.docs_lifecycle_service import verify_doc

    result = verify_doc(root, doc, when=parsed)
    print_result(result, fmt=fmt)
    if not result.ok:
        raise ValidationError("docs verify failed", detail=result.errors[0] if result.errors else "")


@docs_group.command("archive")
@click.argument("doc")
@click.pass_context
def docs_archive(ctx, doc):
    """Move a doc into docs/archive/, leaving a tombstone at the old path.

    The tombstone (a stub with a forward link) keeps inbound links from
    rotting — including links from other repos, which no rewrite pass could
    reach. The manifest entry's path line is updated surgically and the
    derived index is refreshed.

    \b
    Examples:
      grain docs archive docs/working/old_plan.md
      grain docs archive old_plan
    """
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    from grain.services.docs_lifecycle_service import archive_doc

    result = archive_doc(root, doc)
    print_result(result, fmt=fmt)
    if not result.ok:
        raise ValidationError("docs archive failed", detail=result.errors[0] if result.errors else "")


@docs_group.command("promote")
@click.argument("doc")
@click.option(
    "--into", "into", required=True,
    help="Promotion target: an existing canonical doc (path or id) to supersede, or 'new'.",
)
@click.pass_context
def docs_promote(ctx, doc, into):
    """Promote a working doc into canonical — resolves a supersession queue item.

    Mechanics only: the command moves files, stamps Last-verified, archives the
    superseded canon with a supersession note, leaves a tombstone at the old
    working path, and refreshes the manifest/index. Merging content, when
    needed, stays human/agent work done BEFORE promoting.

    \b
    Examples:
      grain docs promote docs/working/spec_v2.md --into docs/canonical/spec.md
      grain docs promote docs/working/new_topic.md --into new
    """
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    from grain.services.docs_lifecycle_service import promote_doc

    result = promote_doc(root, doc, into=into)
    print_result(result, fmt=fmt)
    if not result.ok:
        raise ValidationError("docs promote failed", detail=result.errors[0] if result.errors else "")


@docs_group.command("show")
@click.argument("doc_id")
@click.pass_context
def docs_show(ctx, doc_id):
    """Display doc metadata or path information for a known document."""
    repo = ctx.obj.get("repo") if ctx.obj else None
    fmt = ctx.obj.get("fmt", "text") if ctx.obj else "text"
    root = resolve_repo_root(repo)

    result, record = docs_service.show_doc(root, doc_id)

    if not result.ok:
        for err in result.errors:
            click.echo(f"  error     {err}", err=True)
        raise click.UsageError(f"Doc '{doc_id}' not found")

    if fmt == "json":
        import dataclasses
        data = dataclasses.asdict(result)
        data["doc"] = {
            "id": record.id,
            "path": record.path,
            "layer": record.layer,
            "authority": record.authority,
            "purpose": record.purpose,
            "editable_by_agents": record.editable_by_agents,
            "read_when": record.read_when,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("docs show: ok")
        click.echo(f"  id                  {record.id}")
        click.echo(f"  path                {record.path}")
        click.echo(f"  layer               {record.layer}")
        click.echo(f"  authority           {record.authority}")
        click.echo(f"  purpose             {record.purpose}")
        click.echo(f"  editable_by_agents  {str(record.editable_by_agents).lower()}")
