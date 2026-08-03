# SPDX-FileCopyrightText: 2024-2026 Shaznay Sison
# SPDX-License-Identifier: MIT

"""Shared docs-corpus model — scanning, extraction, and git helpers.

The corpus is the set of markdown documents that make up a project's
documentation body (by default ``docs/canonical/``, ``docs/working/`` and
``docs/archive/``), plus optional external roots registered in the manifest's
``docs_registry.external_roots`` block. This module is pure inspection: it
never writes files (except :func:`set_verified_stamp`, which returns new text
for the caller to write) and degrades gracefully outside a git repository.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

CACHE_REL_PATH = ".grain/docs_corpus_cache.json"
_CACHE_VERSION = 1

# Never descend into these while scanning a root for markdown (external roots
# may be whole repos; vendored/build trees are not documentation).
_PRUNE_DIRS = frozenset({
    ".git", ".grain", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", ".next", ".tox", ".mypy_cache", ".ruff_cache",
})

DEFAULT_CORPUS_DIRS = ("docs/canonical", "docs/working", "docs/archive")

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
# A path-like token: contains a slash, made of path characters, ends with a
# file extension. Excludes URLs, globs, and option/flag strings.
_PATH_LIKE_RE = re.compile(r"^[\w][\w./\-]*/[\w./\-]*\.\w{1,10}$")
_VERIFIED_LINE_RE = re.compile(
    r"^(?:Last[- ]verified|last_verified|verified)\s*:\s*(\d{4}-\d{2}-\d{2})\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_DATE_FMT = "%Y-%m-%d"


# ── Corpus model ──────────────────────────────────────────────────────────────

@dataclass
class CorpusDoc:
    """One markdown document in the docs corpus."""

    abs_path: Path
    rel_path: str            # relative to its root
    root: Path               # the root it was found under
    root_name: str           # "" for the primary repo, else the external root name
    layer: str               # canonical | working | archive | other
    title: str = ""
    headings: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)           # raw link targets
    resolved_links: list[str] = field(default_factory=list)  # repo-relative, normalized
    path_refs: list[str] = field(default_factory=list)       # cited file paths
    last_modified: datetime | None = None
    last_verified: date | None = None
    is_tombstone: bool = False
    _text: str | None = None

    def body(self) -> str:
        """Full document text, read lazily and memoized.

        Cached corpus entries carry extraction fields only; the body is read
        from disk on first access (search scoring, promotion flows)."""
        if self._text is None:
            try:
                self._text = self.abs_path.read_text(encoding="utf-8")
            except Exception:
                self._text = ""
        return self._text


def corpus_dirs(manifest: dict | None) -> list[str]:
    """Corpus directories, from ``docs_registry.corpus_dirs`` or the default."""
    if isinstance(manifest, dict):
        registry = manifest.get("docs_registry")
        if isinstance(registry, dict):
            dirs = registry.get("corpus_dirs")
            if isinstance(dirs, list) and all(isinstance(d, str) for d in dirs) and dirs:
                return list(dirs)
    return list(DEFAULT_CORPUS_DIRS)


def external_roots_from_manifest(root: Path, manifest: dict | None) -> list[tuple[str, Path]]:
    """(name, path) pairs from ``docs_registry.external_roots``; relative paths
    resolve against the repo root. Missing/malformed entries are skipped."""
    roots: list[tuple[str, Path]] = []
    if not isinstance(manifest, dict):
        return roots
    registry = manifest.get("docs_registry")
    if not isinstance(registry, dict):
        return roots
    for entry in registry.get("external_roots") or []:
        if not isinstance(entry, dict):
            continue
        raw_path = entry.get("path", "")
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            p = (root / p).resolve()
        name = str(entry.get("name") or p.name)
        roots.append((name, p))
    return roots


def load_corpus(
    root: Path,
    manifest: dict | None = None,
    external_roots: list[tuple[str, Path]] | None = None,
    use_cache: bool = False,
) -> list[CorpusDoc]:
    """Scan the corpus dirs under ``root`` (plus any external roots) and return
    parsed :class:`CorpusDoc` records. Missing dirs/roots are skipped silently.

    With ``use_cache=True`` the extraction cache at ``.grain/docs_corpus_cache.json``
    is consulted: only files whose (mtime, size) changed since the last scan are
    re-parsed, so refresh cost scales with the diff, not the corpus. The cache
    stores EXTRACTION only (titles, links, refs, stamps) — never audit verdicts.
    """
    cache = _load_cache(root) if use_cache else {}
    entries: dict = cache.get("entries", {}) if isinstance(cache, dict) else {}
    new_entries: dict = {}
    docs: list[CorpusDoc] = []

    def _scan(base_root: Path, rel_dirs: list[str] | None, root_name: str) -> None:
        paths: list[Path] = []
        if rel_dirs is None:
            paths.extend(_walk_markdown(base_root))
        else:
            for rel_dir in rel_dirs:
                base = base_root / rel_dir
                if base.is_dir():
                    paths.extend(_walk_markdown(base))
        for path in paths:
            rel = path.relative_to(base_root).as_posix()
            key = f"{root_name}|{rel}"
            try:
                st = path.stat()
            except OSError:
                continue
            cached = entries.get(key)
            if (
                use_cache
                and isinstance(cached, dict)
                and cached.get("mtime_ns") == st.st_mtime_ns
                and cached.get("size") == st.st_size
            ):
                docs.append(_doc_from_cache(cached, path, base_root, root_name, rel))
                new_entries[key] = cached
                continue
            doc = _parse_doc(path, base_root, root_name)
            docs.append(doc)
            if use_cache:
                new_entries[key] = _doc_to_cache(doc, st.st_mtime_ns, st.st_size)

    _scan(root, corpus_dirs(manifest), "")
    for name, ext_root in external_roots or []:
        if not ext_root.is_dir():
            continue
        _scan(ext_root, None, name)

    if use_cache and new_entries != entries:
        _save_cache(root, new_entries)
    return docs


def _walk_markdown(base: Path) -> list[Path]:
    """All *.md under ``base``, sorted, pruning vendored/build directories."""
    import os

    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in _PRUNE_DIRS)
        for name in sorted(filenames):
            if name.endswith(".md"):
                paths.append(Path(dirpath) / name)
    return sorted(paths)


def _load_cache(root: Path) -> dict:
    path = root / CACHE_REL_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict) or data.get("version") != _CACHE_VERSION:
        return {}
    return data


def _save_cache(root: Path, entries: dict) -> None:
    path = root / CACHE_REL_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        head = _run_git(root, ["rev-parse", "HEAD"])
        payload = {
            "version": _CACHE_VERSION,
            "head": head.strip() if head else "",
            "entries": entries,
        }
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    except OSError:
        pass  # cache is an optimization; never fail the command over it


def _doc_to_cache(doc: CorpusDoc, mtime_ns: int, size: int) -> dict:
    return {
        "mtime_ns": mtime_ns,
        "size": size,
        "layer": doc.layer,
        "title": doc.title,
        "headings": doc.headings,
        "links": doc.links,
        "resolved_links": doc.resolved_links,
        "path_refs": doc.path_refs,
        "last_verified": doc.last_verified.strftime(_DATE_FMT) if doc.last_verified else None,
        "is_tombstone": doc.is_tombstone,
    }


def _doc_from_cache(cached: dict, path: Path, root: Path, root_name: str, rel: str) -> CorpusDoc:
    raw_verified = cached.get("last_verified")
    verified: date | None = None
    if isinstance(raw_verified, str):
        try:
            verified = datetime.strptime(raw_verified, _DATE_FMT).date()
        except ValueError:
            verified = None
    return CorpusDoc(
        abs_path=path,
        rel_path=rel,
        root=root,
        root_name=root_name,
        layer=cached.get("layer") or _layer_of(rel),
        title=cached.get("title", ""),
        headings=list(cached.get("headings") or []),
        links=list(cached.get("links") or []),
        resolved_links=list(cached.get("resolved_links") or []),
        path_refs=list(cached.get("path_refs") or []),
        last_modified=datetime.fromtimestamp(
            cached.get("mtime_ns", 0) / 1e9, tz=timezone.utc
        ),
        last_verified=verified,
        is_tombstone=bool(cached.get("is_tombstone")),
    )


def _parse_doc(path: Path, root: Path, root_name: str) -> CorpusDoc:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        text = ""
    rel_path = path.relative_to(root).as_posix()
    layer = _layer_of(rel_path)
    links = extract_links(text)
    resolved: list[str] = []
    for link in links:
        target = _resolve_link(root, path, link)
        if target:
            resolved.append(target)
    try:
        mtime: datetime | None = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        mtime = None
    return CorpusDoc(
        abs_path=path,
        rel_path=rel_path,
        root=root,
        root_name=root_name,
        layer=layer,
        title=extract_title(text),
        headings=extract_headings(text),
        links=links,
        resolved_links=resolved,
        path_refs=extract_path_refs(text),
        last_modified=mtime,
        last_verified=read_verified_stamp(text),
        is_tombstone="<!-- grain:tombstone -->" in text,
        _text=text,
    )


def _layer_of(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) >= 2 and parts[0] == "docs" and parts[1] in ("canonical", "working", "archive"):
        return parts[1]
    return "other"


def _resolve_link(root: Path, doc_path: Path, link: str) -> str | None:
    """Resolve a raw link target to a root-relative posix path, or None if it
    escapes the root or is a fragment-only link."""
    target = link.split("#", 1)[0]
    if not target:
        return None
    try:
        resolved = (doc_path.parent / target).resolve()
        return resolved.relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


# ── Extraction helpers ────────────────────────────────────────────────────────

def extract_title(text: str) -> str:
    """First H1 heading, or ""."""
    m = _H1_RE.search(text)
    return m.group(1).strip() if m else ""


def extract_headings(text: str) -> list[str]:
    """All headings (any level), in document order."""
    return [m.group(1).strip() for m in _HEADING_RE.finditer(text)]


def extract_links(text: str) -> list[str]:
    """Relative markdown link targets (external URLs excluded)."""
    links: list[str] = []
    for m in _MD_LINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        links.append(target)
    return links


def extract_path_refs(text: str) -> list[str]:
    """Path-like citations in inline code spans (e.g. `scripts/deploy.sh`).

    Only tokens that look like real repo file paths qualify: they contain a
    slash and end in a file extension. URLs, globs, flags, and YAML snippets
    never match.
    """
    refs: list[str] = []
    seen: set[str] = set()
    for m in _CODE_SPAN_RE.finditer(text):
        token = m.group(1).strip()
        if "*" in token or token.startswith(("http://", "https://", "-")):
            continue
        if _PATH_LIKE_RE.match(token) and token not in seen:
            seen.add(token)
            refs.append(token)
    return refs


# ── Verification stamps ───────────────────────────────────────────────────────

def read_verified_stamp(text: str) -> date | None:
    """Return the Last-verified date from a header line or frontmatter, or None."""
    m = _VERIFIED_LINE_RE.search(text)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), _DATE_FMT).date()
    except ValueError:
        return None


def set_verified_stamp(text: str, when: date) -> str:
    """Return new text with the Last-verified stamp set to ``when``.

    Updates an existing stamp in place (header line or frontmatter key);
    otherwise inserts a ``Last-verified:`` line just after the first H1
    (or at the top when there is no H1).
    """
    stamp = when.strftime(_DATE_FMT)
    if _VERIFIED_LINE_RE.search(text):
        def _sub(m: re.Match) -> str:
            line = m.group(0)
            return line[: line.rfind(m.group(1))] + stamp
        return _VERIFIED_LINE_RE.sub(_sub, text, count=1)

    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, f"\nLast-verified: {stamp}\n")
            return "".join(lines)
    return f"Last-verified: {stamp}\n\n" + text


# ── Git helpers ───────────────────────────────────────────────────────────────

def _run_git(root: Path, args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_last_commit_date(root: Path, rel_path: str) -> date | None:
    """Date of the last commit touching ``rel_path``, or None (graceful)."""
    out = _run_git(root, ["log", "-1", "--format=%cs", "--", rel_path])
    if not out or not out.strip():
        return None
    try:
        return datetime.strptime(out.strip(), _DATE_FMT).date()
    except ValueError:
        return None


def load_git_commit_index(
    root: Path, max_commits: int = 5000
) -> list[tuple[date, frozenset[str]]] | None:
    """One batched ``git log`` walk: (commit date, files touched) per commit,
    newest first. Returns None outside a git repo (graceful degradation).

    Audit signals derive BOTH per-file last-commit dates and churn counts from
    this single subprocess call, so audit cost scales with history size once —
    not with docs × references.
    """
    out = _run_git(
        root,
        ["log", f"-{max_commits}", "--format=%x01%cs", "--name-only"],
    )
    if out is None:
        return None
    index: list[tuple[date, frozenset[str]]] = []
    current_date: date | None = None
    current_files: set[str] = set()
    for line in out.splitlines():
        if line.startswith("\x01"):
            if current_date is not None:
                index.append((current_date, frozenset(current_files)))
            try:
                current_date = datetime.strptime(line[1:].strip(), _DATE_FMT).date()
            except ValueError:
                current_date = None
            current_files = set()
        elif line.strip() and current_date is not None:
            current_files.add(line.strip())
    if current_date is not None:
        index.append((current_date, frozenset(current_files)))
    return index


def last_commit_dates(index: list[tuple[date, frozenset[str]]]) -> dict[str, date]:
    """Per-file date of the most recent commit touching it (index is newest-first)."""
    dates: dict[str, date] = {}
    for commit_date, files in index:
        for f in files:
            if f not in dates:
                dates[f] = commit_date
    return dates


def churn_since(
    index: list[tuple[date, frozenset[str]]], targets: set[str], since: date
) -> int:
    """Commits in the index strictly after ``since`` touching any target."""
    return sum(
        1 for commit_date, files in index
        if commit_date > since and files & targets
    )


def git_churn_since(root: Path, rel_paths: list[str], since: str) -> int | None:
    """Number of commits touching any of ``rel_paths`` since ``since``
    (YYYY-MM-DD), or None when git is unavailable / not a repo."""
    if not rel_paths:
        return 0
    out = _run_git(
        root,
        ["log", "--oneline", f"--since={since}", "--", *rel_paths],
    )
    if out is None:
        return None
    return len([line for line in out.splitlines() if line.strip()])
