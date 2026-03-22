# Feature: audit-remediation

## Overview
Drive the project from the current audit result (`WARNING`, 6.4/10) to a re-audit target of zero findings, enforced quality gates, and measurable mesh data. "100%" here means zero accepted audit findings on the next audit date, not a permanent guarantee against future dependency drift.

## Phases
| # | Name | Status | Plan File | Summary |
|---|------|--------|-----------|---------|
| 1 | Quality Gate Foundation | ⬚ Pending | plan-audit-remediation-phase1.md | Fix fail-open startup path and enforce CI/test/lint/security gates |
| 2 | Scanner Core Simplification | ⬚ Pending | plan-audit-remediation-phase2.md | Reduce `FolderScanner` complexity and replace silent failure paths |
| 3 | Storage View Decomposition | ⬚ Pending | plan-audit-remediation-phase3.md | Split `StorageView` into smaller UI/controller helpers with tests |
| 4 | Lint and Config Closure | ⬚ Pending | plan-audit-remediation-phase4.md | Make Flake8 config effective and burn down source/test lint debt |
| 5 | Docs, Release, and Compliance | ⬚ Pending | plan-audit-remediation-phase5.md | Refresh README, test report, license/env docs, release notes |
| 6 | Metrics and Re-Audit Readiness | ⬚ Pending | plan-audit-remediation-phase6.md | Add `.rune/metrics` visibility, rerun checks, and prepare audit evidence |

## Key Decisions
- Use a full remediation program, not surgical patches. Completeness: 9.5/10 (human: ~2-3 days / AI: ~4-6 sessions).
- Define success as zero open findings in the next audit plus green verification (`pytest`, `flake8`, `bandit`, complexity threshold, release workflow).
- Fix governance first: if CI and startup behavior stay weak, later refactors can regress silently.
- Refactor scanner and storage view in separate phases to keep risk isolated and reviews smaller.
- Treat lint as product health, not cosmetics: only clean it after config is made authoritative.

## Decision Compliance
- Decisions (locked): preserve Windows desktop app architecture, PyQt6 UI, existing test suite, and current packaging path (PyInstaller + NSIS).
- Discretion (agent): add stricter CI gates, metrics capture, and documentation coverage because they directly close audit gaps.
- Deferred: dependency major-version upgrades beyond what is needed for audit closure; broad UI redesign unrelated to findings.

## Architecture
Audit findings -> governance fixes -> core scan refactor -> UI decomposition -> lint/doc closure -> verification + metrics -> re-audit

## Workflow Registry
### View 1: By Workflow
| Workflow | Entry Point | Components | Exit Point | Phase |
|----------|-------------|------------|------------|-------|
| App startup | `src/main.py` -> `App.start()` | `app`, `registry`, `storage_monitor` | single instance, monitored app | 1 |
| Release build | `.github/workflows/release.yml` | pytest/flake8/bandit/build | tagged artifact | 1,5 |
| Folder scan | `StorageView._start_realtime_scan()` | `storage_view`, `folder_scanner` | populated tree | 2,3 |
| Audit closure | local checks + report refresh | docs, metrics, reports | PASS-ready evidence | 4,5,6 |

### View 2: By Component
| Component | Used By | Owner Phase | Status |
|-----------|---------|-------------|--------|
| `src/app.py` | startup workflow | 1 | Planned |
| `src/features/folder_scanner/service.py` | folder scan | 2 | Planned |
| `src/ui/views/storage_view.py` | folder scan | 3 | Planned |
| `pyproject.toml` + lint config | audit closure | 4 | Planned |
| docs / reports / workflow | release + audit closure | 5 | Planned |
| `.rune/metrics/*` | audit closure | 6 | Missing |

### View 3: By User Journey
| Journey | Steps | Happy Path | Error Path |
|---------|------|------------|------------|
| Launch app | start -> lock -> monitor -> tray/ui | one instance only | lock failure stops launch |
| Scan storage | choose drive -> realtime scan -> expand -> delete/open | responsive tree | tracked scan errors, no silent skips |
| Ship release | tag -> CI checks -> package -> release | gated publish | CI fails before artifact creation |

### View 4: By State
| Step | User Sees | Code State | Evidence |
|------|-----------|------------|----------|
| After startup | one tray app | single-instance lock held | tests + logs |
| During scan | progressive results | buffered realtime scan | tests + perf checks |
| Before release | green pipeline | gates enforced | CI workflow + local reruns |
| Next audit | PASS / zero findings | docs + metrics current | audit bundle |

## Dependencies / Risks
- Risk: scanner/UI refactors break behavior. Mitigation: preserve current tests, add characterization tests before deeper changes.
- Risk: lint cleanup becomes unbounded. Mitigation: lock config first, then burn down by module.
- Risk: "100%" goal drifts. Mitigation: exit criteria are explicit and measurable before re-audit.
