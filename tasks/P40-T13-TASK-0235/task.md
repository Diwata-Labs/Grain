# Task: OIDC Trusted Publishing for grain-contracts + grain-core

## Metadata
- **ID:** TASK-0235
- **Status:** review
- **Mode:** simple
- **Phase:** Phase 40 — Release Hygiene & DX
- **Backlog:** P40-T13
- **Dependencies:** none
- **Primary Adapter:** none
- **Secondary Adapters:** none

## Objective
The `grain-contracts 0.2.0` release failed at `Publish to PyPI` with a 403 — the
`PYPI_TOKEN_GRAIN_CONTRACTS` secret had expired (it worked for 0.1.0 on 2026-07-16). Move
`grain-contracts` and `grain-core` off expiring API tokens onto **PyPI OIDC Trusted Publishing**
so releases authenticate via GitHub's OIDC identity and no token can ever expire again.

## Why This Task Exists
Recurring token-expiry breaks the two zero-dep packages Diwa/Assay/Daemon depend on. Trusted
Publishing is the durable fix (no long-lived secret). grain-kit / assay / pulse stay on tokens for
now and migrate the same way later.

## Scope
- `.github/workflows/release-python.yml`: add job `permissions: id-token: write`; publish
  `grain-contracts`/`grain-core` with `uv publish --trusted-publishing always` (no token) and the
  token products with `--trusted-publishing never` (so the id-token permission can't divert them
  onto un-configured OIDC → 403).
- Operator (out-of-repo): add a Trusted Publisher on each PyPI project (owner Diwata-Domains, repo
  Diwata-Labs, workflow `release-python.yml`, no environment).
- Re-run the `grain-contracts-v0.2.0` release once the publisher is configured.

## Constraints
- Must NOT break grain-kit / assay / pulse token releases (they stay `--trusted-publishing never`).
- No code changes to the packages; publish-mechanism only.

## Escalation Conditions
- If PyPI rejects the OIDC exchange after the publisher is configured (audience/subject mismatch),
  capture the 403 detail and reconcile the trusted-publisher fields.
