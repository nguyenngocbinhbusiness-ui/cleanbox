# Phase 5: Docs, Release, and Compliance

## Goal
Close the documentation and compliance findings, then turn the release workflow into the final fully gated ship path using the green lint baseline from Phase 4.

## Data Flow
```text
Source + tests + workflow state
    -> README / docs / reports / license / env example updates
    -> release workflow consumes verify_release.py + flake8
    -> tagged release blocks on green checks
    -> docs describe the actual ship path
```

## Code Contracts
```text
README.md must document install, run, test, lint, security scan, build, and release steps.
LICENSE must match the MIT declaration in pyproject.toml.
.env.example must document supported app-specific environment variables.
release.yml must gate packaging on pytest + flake8 + bandit + build smoke.
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Add compliance artifacts
  - Req: AUD-006, AUD-007
  - File: `LICENSE` (new)
  - File: `.env.example` (new)
  - Test: N/A
  - Verify: `Get-Content LICENSE; Get-Content .env.example`
  - Commit: `docs(compliance): add MIT license and environment example`
  - Logic: add MIT text and document `CLEANBOX_SCANNER_WORKERS` plus "uses standard Windows env vars" note.
  - Edge: no fake secrets, no undocumented unsupported env knobs.
- [ ] Task 2 - Refresh README and release documentation
  - Req: AUD-006
  - File: `README.md` (modify)
  - File: `docs/requirements.md` (modify if terminology/version references changed)
  - File: `docs/release-process.md` (new)
  - Test: N/A
  - Verify: `Get-Content README.md; Get-Content docs\release-process.md`
  - Commit: `docs(readme): document testing build and release workflow`
  - Logic: cover setup, local run, pytest, flake8, bandit, packaging, and tagged release process.
  - Edge: Windows-specific commands, parent `.venv` path, release artifact names.

### Wave 2 (depends on Phase 4 being complete)
- [ ] Task 3 - Enable final release lint/security/test/build gating
  - Req: AUD-002, AUD-006
  - depends_on: [Task 1, Task 2]
  - File: `.github/workflows/release.yml` (modify)
  - File: `quality/verify_release.py` (modify)
  - Test: `tests/integration/test_additional_integration.py` (modify)
  - Verify: `..\.venv\Scripts\python.exe quality\verify_release.py --include-flake8`
  - Commit: `ci(release): require full lint test security and build verification before ship`
  - Logic: make flake8 mandatory now that Phase 4 is green; keep one script as the release gate.
  - Edge: Windows quoting, optional local flag defaults, workflow caching.

### Wave 3 (depends on Wave 2)
- [ ] Task 4 - Refresh checked-in reports and release notes
  - Req: AUD-006
  - depends_on: [Task 3]
  - File: `tests/reports/test_report.md` (modify)
  - File: `CHANGELOG.md` (modify if release/process wording changes)
  - Test: N/A
  - Verify: `Get-Content tests\reports\test_report.md`
  - Commit: `docs(reports): refresh checked-in test evidence and release notes`
  - Logic: replace stale 495-test report with current numbers and current process notes.
  - Edge: keep report factual; do not invent pass counts that were not rerun.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| README steps drift from reality | update commands to match actual repo layout | Documentation defect |
| `.env.example` implies unsupported config | remove it or narrow to supported variables only | Documentation defect |
| Release gate still allows packaging on failed lint | workflow is incomplete; do not ship | CI defect |
| Checked-in report numbers are stale | rerun the relevant verification before updating | Evidence defect |

## Rejection Criteria (DO NOT)
- Do not create placeholder docs that omit actual commands.
- Do not add fake environment variables just to satisfy the audit note.
- Do not update test-report counts without rerunning or referencing a specific fresh log.
- Do not bypass the unified `quality/verify_release.py` entrypoint.

## Cross-Phase Context
- Assumes Phase 4 delivered a green `flake8 src tests`.
- Exports final release-process docs and compliance files for Phase 6 evidence capture.
- Phase 6 uses the refreshed docs and reports as part of the re-audit bundle.

## Acceptance Criteria
- [ ] `LICENSE` exists and matches MIT metadata.
- [ ] `.env.example` documents supported environment configuration only.
- [ ] README and release docs cover install, test, lint, security scan, build, and release.
- [ ] Release workflow blocks on pytest + flake8 + bandit + build smoke.
- [ ] Checked-in test/report artifacts are current and evidence-backed.

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-002 | Final release workflow must block on full verification | 3 | `tests/integration/test_additional_integration.py` + `quality/verify_release.py --include-flake8` | ⬚ |
| AUD-006 | Documentation must cover testing/build/release and reports must be current | 2, 4 | Manual doc verification + fresh report evidence | ⬚ |
| AUD-007 | Compliance artifacts must exist | 1 | Manual verification | ⬚ |

## Files Touched
- `LICENSE` - new
- `.env.example` - new
- `README.md` - modify
- `docs/requirements.md` - modify if needed
- `docs/release-process.md` - new
- `.github/workflows/release.yml` - modify
- `quality/verify_release.py` - modify
- `tests/integration/test_additional_integration.py` - modify
- `tests/reports/test_report.md` - modify
- `CHANGELOG.md` - modify if needed
