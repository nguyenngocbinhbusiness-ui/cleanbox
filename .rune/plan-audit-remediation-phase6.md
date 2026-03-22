# Phase 6: Metrics and Re-Audit Readiness

## Goal
Create the missing `.rune/metrics` visibility, produce a reproducible audit-evidence bundle, and rerun the full verification stack so the next audit can legitimately score at 100%.

## Data Flow
```text
Verification runs -> quality evidence script
                  -> .rune/metrics/*.json/jsonl
                  -> quality/reports/re_audit_readiness.md
                  -> refreshed audit journal
                  -> next audit consumes evidence instead of assumptions
```

## Code Contracts
```python
# quality/capture_audit_metrics.py
def append_session_metrics(*, duration_seconds: float, tool_calls: int, skills: list[str]) -> None: ...
def write_skill_summary() -> None: ...

# quality/build_reaudit_bundle.py
def run_reaudit_bundle() -> int:
    """Run pytest, flake8, bandit, radon, and quality reports; write markdown summary."""
```

```text
.rune/metrics/skills.json
.rune/metrics/sessions.jsonl
.rune/metrics/chains.jsonl
quality/reports/re_audit_readiness.md
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Add metrics capture utilities and file schema
  - Req: AUD-008
  - File: `quality/capture_audit_metrics.py` (new)
  - File: `.rune/metrics/skills.json` (new seed file)
  - File: `.rune/metrics/sessions.jsonl` (new seed file)
  - File: `.rune/metrics/chains.jsonl` (new seed file)
  - File: `.rune/metrics/README.md` (new)
  - Test: `tests/integration/test_additional_integration.py` (modify or add schema assertions)
  - Verify: `..\.venv\Scripts\python.exe quality\capture_audit_metrics.py --help`
  - Commit: `chore(metrics): add rune metrics capture for audit visibility`
  - Logic: make audit-required metrics files exist with a documented format and append behavior.
  - Edge: first-run file creation, repeated appends, invalid JSON recovery.
- [ ] Task 2 - Create re-audit bundle generator
  - Req: AUD-009
  - File: `quality/build_reaudit_bundle.py` (new)
  - File: `quality/reports/re_audit_readiness.md` (generated/update target)
  - Test: `tests/integration/test_additional_integration.py` (modify)
  - Verify: `..\.venv\Scripts\python.exe quality\build_reaudit_bundle.py`
  - Commit: `chore(quality): add reproducible re-audit evidence bundle`
  - Logic: run and summarize `pytest`, `flake8`, `bandit`, and `radon` in one report.
  - Edge: subprocess failure propagation, partial report generation, Windows command quoting.

### Wave 2 (depends on Wave 1 and prior phases being complete)
- [ ] Task 3 - Capture a fresh full verification run
  - Req: AUD-008, AUD-009
  - depends_on: [Task 1, Task 2]
  - File: `.pytest_full_after.log` (refresh)
  - File: `quality/reports/re_audit_readiness.md` (refresh)
  - File: `.rune/journal/audit-2026-03-22.md` (modify with closure summary or superseding note)
  - Test: verification commands are the test
  - Verify: `..\.venv\Scripts\python.exe -m pytest -q && ..\.venv\Scripts\python.exe -m flake8 src tests && ..\.venv\Scripts\python.exe -m bandit -r src -f txt && ..\.venv\Scripts\python.exe -m radon cc src -s -a`
  - Commit: `chore(audit): capture green verification evidence for re-audit`
  - Logic: run the full stack only after all prior phases are complete; refresh evidence files with actual results.
  - Edge: flaky UI tests, log truncation, rerun requirement when counts change mid-phase.

### Wave 3 (depends on Wave 2)
- [ ] Task 4 - Prepare the next audit handoff package
  - Req: AUD-009
  - depends_on: [Task 3]
  - File: `AUDIT-REPORT.md` (modify only if recording resolved-state appendix or superseding note)
  - File: `.rune/plan-audit-remediation.md` (modify statuses)
  - Test: N/A
  - Verify: `Get-Content quality\reports\re_audit_readiness.md`
  - Commit: `docs(audit): mark remediation completion and package re-audit evidence`
  - Logic: update plan statuses, link metrics/report locations, and leave a clean handoff for the actual next audit run.
  - Edge: avoid rewriting historical findings; append closure notes instead.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| Metrics files are missing or corrupt | recreate seed files and continue with valid JSON | Recoverable tooling condition |
| One verification command fails | bundle exits non-zero and clearly names the failing step | Verification failure |
| Fresh test totals differ from old report | update evidence files with new factual values | No error |
| Plan statuses and evidence drift apart | fix the plan/handoff before declaring readiness | Process error |

## Rejection Criteria (DO NOT)
- Do not fabricate metrics entries just to satisfy the audit phase.
- Do not mark the plan complete before the full verification stack is green.
- Do not overwrite historical audit findings; append closure evidence instead.
- Do not skip radon or bandit on the final bundle because earlier phases looked clean.

## Cross-Phase Context
- Assumes Phases 1-5 are complete and green.
- Exports `.rune/metrics` data and a single `re_audit_readiness.md` handoff for the next audit session.
- This is the last phase; after completion, the master plan statuses should be updated to `✅`.

## Acceptance Criteria
- [ ] `.rune/metrics` exists with documented schemas and real captured data.
- [ ] A single command produces the re-audit evidence bundle.
- [ ] Full verification stack is green on current code.
- [ ] Master plan and journal reflect completed remediation state.
- [ ] Next audit can cite fresh metrics and verification logs instead of "no data yet".

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-008 | Populate `.rune/metrics` for audit visibility | 1, 3 | Metrics script + schema assertions | ⬚ |
| AUD-009 | Produce reproducible green evidence for next audit | 2, 3, 4 | Full verification bundle | ⬚ |

## Files Touched
- `quality/capture_audit_metrics.py` - new
- `quality/build_reaudit_bundle.py` - new
- `.rune/metrics/skills.json` - new
- `.rune/metrics/sessions.jsonl` - new
- `.rune/metrics/chains.jsonl` - new
- `.rune/metrics/README.md` - new
- `quality/reports/re_audit_readiness.md` - generate/update
- `.pytest_full_after.log` - refresh
- `.rune/journal/audit-2026-03-22.md` - modify
- `AUDIT-REPORT.md` - append/update only if needed
- `.rune/plan-audit-remediation.md` - modify statuses
