# Audit Remediation Progress - 2026-03-22

## Completed
- Phase 1: release gate foundation
  - `src/app.py` now fails closed on unrecoverable single-instance lock errors.
  - `quality/verify_release.py` added and wired into `.github/workflows/release.yml`.
- Phase 2: scanner core simplification
  - `src/features/folder_scanner/service.py` refactored into smaller helpers.
  - `src/features/folder_scanner/scan_helpers.py` added for timestamp parsing/formatting.
  - `_scan_recursive` reduced to radon `B (10)`.
- Phase 3: storage view decomposition
  - `src/ui/views/storage_view_tree.py` added for tree building and numeric tree items.
  - `src/ui/views/storage_view_actions.py` added for recycle/open shell actions.
  - `src/ui/views/storage_view.py` delegates tree/action work to helpers.

## Verification State
- `python quality/verify_release.py` passes.
- `pytest -q` passes: `564 passed`.
- `flake8 src` passes with authoritative `.flake8` config.
- Remaining recurring noise:
  - Windows pytest temp-dir cleanup still emits `PermissionError` during atexit cleanup.
  - This does not fail the test run.

## Phase 4 Status
- `.flake8` created as the authoritative Flake8 config.
- `pyproject.toml` Flake8 section aligned with `.flake8`.
- `src` lint backlog is closed.
- `tests` lint backlog remains large and is concentrated in legacy test modules:
  - unused imports/locals
  - import-order violations
  - semicolon-compressed test statements in older e2e files
  - a few remaining long lines and lambda-style assertions

## Next Recommended Work
1. Continue Phase 4 on `tests/` only.
2. Start with `tests/conftest.py`, `tests/component/*`, and `tests/e2e/test_business_requirements.py`.
3. Then clean semicolon-heavy e2e suites: `tests/e2e/test_ui_elements.py`, `tests/e2e/test_ui_implicit.py`, `tests/e2e/test_use_cases.py`.
4. Finish remaining unit-test unused imports and local variable cleanup.
5. Re-run:
   - `python -m flake8 tests`
   - `python -m flake8 src tests`
   - `python -m pytest -q`
