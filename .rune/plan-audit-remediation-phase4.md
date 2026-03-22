# Phase 4: Lint and Config Closure

## Goal
Make Flake8 configuration authoritative for the installed toolchain, then burn down the current source and test lint backlog until `flake8 src tests` passes cleanly.

## Data Flow
```text
.flake8 + pyproject -> flake8 invocation
                    -> source batch cleanup
                    -> test batch cleanup
                    -> full-project flake8 pass
                    -> release workflow can safely enable lint gating
```

## Code Contracts
```ini
# .flake8
[flake8]
max-line-length = 120
exclude = .venv,__pycache__,.git,.pytest_cache
```

```python
# No new runtime API. This phase changes formatting, unused imports, and config only.
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Make lint config explicit for the current Flake8 install
  - Req: AUD-005
  - File: `.flake8` (new)
  - File: `pyproject.toml` (modify for consistency only)
  - Test: N/A
  - Verify: `..\.venv\Scripts\python.exe -m flake8 --version`
  - Commit: `chore(lint): add authoritative flake8 config for local and CI use`
  - Logic: keep one effective config source; mirror, do not conflict.
  - Edge: Windows path exclusions, tests included intentionally.

### Wave 2 (depends on Wave 1)
- [ ] Task 2 - Clean lint in app/core/shared modules
  - Req: AUD-005
  - depends_on: [Task 1]
  - File: `src/app.py` (modify)
  - File: `src/main.py` (modify)
  - File: `src/shared/constants.py` (modify)
  - File: `src/shared/config/manager.py` (modify)
  - File: `src/shared/elevation.py` (modify)
  - File: `src/shared/registry.py` (modify)
  - File: `src/shared/utils.py` (modify)
  - Test: `tests/unit/test_app_coverage_final.py`, `tests/unit/test_config_registry_complete.py`, `tests/unit/test_shared_utils.py`
  - Verify: `..\.venv\Scripts\python.exe -m flake8 src\app.py src\main.py src\shared`
  - Commit: `style(core): resolve lint violations in app entry and shared modules`
  - Logic: fix whitespace, imports, line length, and unused symbols without changing behavior.
- [ ] Task 3 - Clean lint in feature modules
  - Req: AUD-005
  - depends_on: [Task 1]
  - File: `src/features/cleanup/__init__.py` (modify)
  - File: `src/features/cleanup/service.py` (modify)
  - File: `src/features/cleanup/worker.py` (modify)
  - File: `src/features/folder_scanner/service.py` (modify)
  - File: `src/features/notifications/service.py` (modify)
  - File: `src/features/storage_monitor/service.py` (modify)
  - File: `src/features/storage_monitor/utils.py` (modify)
  - Test: `tests/unit/test_cleanup_module_complete.py`, `tests/unit/test_folder_scanner_coverage.py`, `tests/unit/test_notifications_coverage.py`, `tests/unit/test_storage_monitor_coverage.py`
  - Verify: `..\.venv\Scripts\python.exe -m flake8 src\features`
  - Commit: `style(features): resolve lint violations in cleanup scanner and monitoring modules`
  - Logic: remove unused locals/imports and align line length/blank-line rules.

### Wave 3 (depends on Wave 2)
- [ ] Task 4 - Clean lint in UI modules
  - Req: AUD-005
  - depends_on: [Task 2, Task 3]
  - File: `src/ui/main_window.py` (modify)
  - File: `src/ui/tray_icon.py` (modify)
  - File: `src/ui/components/sidebar.py` (modify)
  - File: `src/ui/views/cleanup_view.py` (modify)
  - File: `src/ui/views/settings_view.py` (modify)
  - File: `src/ui/views/storage_view.py` (modify)
  - File: `src/ui/views/storage_view_tree.py` (modify if created in Phase 3)
  - File: `src/ui/views/storage_view_actions.py` (modify if created in Phase 3)
  - Test: `tests/unit/test_storage_view_coverage.py`, `tests/unit/test_settings_view_coverage.py`, `tests/unit/test_tray_icon.py`
  - Verify: `..\.venv\Scripts\python.exe -m flake8 src\ui`
  - Commit: `style(ui): resolve lint violations in main window tray and views`
  - Logic: finish source-tree lint closure after Phase 3 extraction.

### Wave 4 (depends on Wave 3)
- [ ] Task 5 - Clean lint in test support, component, and e2e modules
  - Req: AUD-005
  - depends_on: [Task 4]
  - File: `tests/conftest.py` (modify)
  - File: `tests/component/test_component_edge_cases.py` (modify)
  - File: `tests/component/test_ui_components.py` (modify)
  - File: `tests/e2e/test_business_requirements.py` (modify)
  - Test: those files
  - Verify: `..\.venv\Scripts\python.exe -m flake8 tests\conftest.py tests\component tests\e2e\test_business_requirements.py`
  - Commit: `style(tests): resolve lint violations in fixtures component and e2e tests`
  - Logic: remove unused imports, indentation issues, and whitespace noise.
- [ ] Task 6 - Clean lint in remaining unit tests and enforce full-project pass
  - Req: AUD-005
  - depends_on: [Task 5]
  - File: `tests/unit/test_registry_comprehensive.py` (modify)
  - File: `tests/unit/test_remaining_coverage.py` (modify)
  - File: `tests/unit/test_settings_view_coverage.py` (modify)
  - File: `tests/unit/test_shared_utils.py` (modify)
  - File: `tests/unit/test_storage_monitor_coverage.py` (modify)
  - File: `tests/unit/test_storage_utils_coverage.py` (modify)
  - File: `tests/unit/test_storage_view_coverage.py` (modify)
  - File: `tests/unit/test_tray_icon.py` (modify)
  - File: `tests/unit/test_ui_error_coverage.py` (modify)
  - Test: those files
  - Verify: `..\.venv\Scripts\python.exe -m flake8 src tests`
  - Commit: `style(tests): finish lint cleanup and enforce full-project flake8 pass`
  - Logic: resolve the remaining reported unit-test lint failures, then confirm the full tree is clean.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| `.flake8` conflicts with `pyproject.toml` | keep one source authoritative and document it | Configuration error |
| Lint cleanup changes behavior | tests fail; revert and fix precisely | Regression |
| New helper files from Phase 3 are absent | skip those file edits and keep commands targeted to existing files | No error |

## Rejection Criteria (DO NOT)
- Do not suppress lint errors by excluding active source or test directories.
- Do not use blanket `noqa` except for truly justified cases with comments.
- Do not mass-autoformat without rerunning relevant tests.
- Do not enable release lint gating until `flake8 src tests` is actually green.

## Cross-Phase Context
- Assumes Phases 2 and 3 finish the structural refactors first.
- Exports a green `flake8 src tests` baseline required by Phase 5 release gating.
- Phase 6 depends on this phase to produce clean verification evidence.

## Acceptance Criteria
- [ ] `.flake8` is present and effective for local runs.
- [ ] `flake8 src tests` passes cleanly.
- [ ] No behavior regressions are introduced by lint cleanup.
- [ ] Source and test modules named in the audit are clean.

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-005 | Make lint config effective and clear the lint backlog | 1, 2, 3, 4, 5, 6 | `flake8 src tests` + targeted pytest runs | ⬚ |

## Files Touched
- `.flake8` - new
- `pyproject.toml` - modify
- `src/app.py` - modify
- `src/main.py` - modify
- `src/shared/*` - modify targeted files listed above
- `src/features/*` - modify targeted files listed above
- `src/ui/*` - modify targeted files listed above
- `tests/conftest.py` - modify
- `tests/component/*` - modify targeted files listed above
- `tests/e2e/test_business_requirements.py` - modify
- `tests/unit/*` - modify targeted files listed above
