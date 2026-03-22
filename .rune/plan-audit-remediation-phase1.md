# Phase 1: Quality Gate Foundation

## Goal
Make startup fail closed on unrecoverable single-instance lock errors, and establish the first blocking quality gates so releases cannot ship without core verification.

## Data Flow
```text
App launch -> App._acquire_single_instance()
          -> lock available? -> continue startup
          -> lock stale? -> recover -> continue startup
          -> unrecoverable lock error -> stop launch (exit code != 0)

Tag push -> release workflow -> quality/verify_release.py
        -> pytest + bandit + build smoke
        -> pass -> package artifacts
        -> fail -> stop release
```

## Code Contracts
```python
# src/app.py
def _acquire_single_instance(self) -> bool:
    """Return True only when this process safely owns the lock."""

# quality/verify_release.py
def run_checks(include_flake8: bool = False) -> int:
    """Run release-blocking checks and return process exit code."""

def main() -> int:
    """CLI entry for CI and local release verification."""
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Add startup lock characterization tests
  - Req: AUD-001
  - File: `tests/unit/test_app_complex_flows.py` (modify)
  - File: `tests/integration/test_app_integration.py` (modify)
  - Test: these files
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_app_complex_flows.py tests\integration\test_app_integration.py -q`
  - Commit: `test(app): cover unrecoverable single-instance lock failures`
  - Logic: cover active instance, stale lock recovery, and unrecoverable listen failure.
  - Edge: socket timeout, failed stale-lock removal, unexpected `QLocalServer` error string.
- [ ] Task 2 - Create reusable release verification entrypoint
  - Req: AUD-002
  - File: `quality/verify_release.py` (new)
  - Test: `tests/integration/test_additional_integration.py` (modify)
  - Verify: `..\.venv\Scripts\python.exe quality\verify_release.py`
  - Commit: `build(quality): add reusable release verification script`
  - Logic: run `pytest`, `bandit -r src`, and a PyInstaller smoke command; leave `flake8` optional until Phase 4 is complete.
  - Edge: subprocess non-zero exit, missing tool, Windows-only build path.

### Wave 2 (depends on Wave 1)
- [ ] Task 3 - Make single-instance acquisition fail closed
  - Req: AUD-001
  - depends_on: [Task 1]
  - File: `src/app.py` (modify)
  - File: `src/main.py` (modify)
  - Test: `tests/unit/test_app_complex_flows.py`, `tests/integration/test_app_integration.py`
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_app_complex_flows.py tests\integration\test_app_integration.py -q`
  - Commit: `fix(app): fail closed when single-instance lock cannot be safely acquired`
  - Logic: return `False` or exit non-zero on unrecoverable lock errors; log clear diagnostics.
  - Edge: stale-lock cleanup succeeds, stale-lock cleanup fails, second instance show command errors.

### Wave 3 (depends on Wave 1 and Wave 2)
- [ ] Task 4 - Gate release packaging on reusable verification
  - Req: AUD-002
  - depends_on: [Task 2, Task 3]
  - File: `.github/workflows/release.yml` (modify)
  - Test: `tests/integration/test_additional_integration.py` (modify or add workflow command assertions)
  - Verify: `Get-Content .github\workflows\release.yml`
  - Commit: `ci(release): block packaging on startup and security verification`
  - Logic: add a pre-package step that runs `quality/verify_release.py`; artifact steps must not execute when verification fails.
  - Edge: workflow path quoting on Windows runners, PyInstaller smoke failure, skipped artifact creation.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| Another instance is alive | send `show`, stop startup cleanly | No error |
| Lock exists but is stale | remove stale lock, retry listen once | Recoverable startup condition |
| Listen still fails after stale cleanup | stop startup; do not run duplicate app | RuntimeError / non-zero exit |
| CI quality script returns non-zero | workflow stops before packaging | CI failure |
| PyInstaller smoke tool missing | verification script returns non-zero with actionable message | ToolingError |

## Performance Constraints
| Metric | Requirement | Why |
|--------|-------------|-----|
| Startup lock path | < 3s worst case | Avoid tray app feeling hung |
| Release verification overhead | < 10 min on CI | Keep release flow usable |

## Rejection Criteria (DO NOT)
- Do not keep `return True` on unrecoverable lock failure.
- Do not silence startup errors only in logs; return a failing process status too.
- Do not wire release packaging before the verification step.
- Do not introduce a second verification script for CI and another one for local use.

## Cross-Phase Context
- Assumes current startup and workflow files remain the entry points.
- Exports a stable `quality/verify_release.py` contract that later phases expand with `flake8`.
- Phase 5 depends on this phase to wire the final full release gate.

## Acceptance Criteria
- [ ] Unrecoverable single-instance lock errors stop startup instead of allowing duplicate instances.
- [ ] Local and CI release verification share one script.
- [ ] Release workflow runs blocking checks before packaging.
- [ ] Phase-specific tests pass.
- [ ] `bandit -r src` still reports no medium/high issues.

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-001 | Fail closed on unrecoverable single-instance errors | 1, 3 | `tests/unit/test_app_complex_flows.py`, `tests/integration/test_app_integration.py` | ⬚ |
| AUD-002 | Add blocking release verification before packaging | 2, 4 | `tests/integration/test_additional_integration.py` | ⬚ |

## Files Touched
- `src/app.py` - modify
- `src/main.py` - modify
- `quality/verify_release.py` - new
- `.github/workflows/release.yml` - modify
- `tests/unit/test_app_complex_flows.py` - modify
- `tests/integration/test_app_integration.py` - modify
- `tests/integration/test_additional_integration.py` - modify
