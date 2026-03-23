# RESCUE-STATE

- health_score_baseline: 53.77
- health_score_current: 53.77
- current_phase: RECON complete
- sessions_used: 1
- autopsy_artifact: `quality/reports/rescue_autopsy.json`

## Modules To Rescue (Worst First)

| # | Module | Health | LOC | Pattern | Status |
|---|---|---:|---:|---|---|
| 1 | ui.views | 40.24 | 2283 | Strangler Fig | pending |
| 2 | shared | 49.28 | 783 | Strangler Fig | pending |
| 3 | features.folder_scanner | 55.5 | 851 | Strangler Fig | pending |

## Dependency Report

- requirements_count: 7
- outdated_count: 4
- pip_audit_available: False
- vulnerability_scan: not_run
- outdated_packages:
  - PyQt6 6.10.0 -> 6.10.2
  - pillow 12.0.0 -> 12.1.1
  - win11toast 0.36.2 -> 0.36.3
  - psutil 7.1.3 -> 7.2.2

## Notes

- Baseline tag points to current HEAD commit; working tree currently has uncommitted rescue edits.
- Surgery must wait until safety net checkpoint (characterization tests + rune-rescue-safety-net tag).
