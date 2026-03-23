# CleanBox Agent Context

## Project Summary
- Name: `cleanbox`
- Version: `1.0.19`
- Platform: Windows desktop utility (PyQt6)
- Purpose: Monitor disk space, notify users, and run cleanup actions from tray/UI.

## Repository Layout
- `src/app.py`: app bootstrap, single-instance guard, cleanup orchestration.
- `src/features/`: domain services (`cleanup`, `folder_scanner`, `storage_monitor`).
- `src/shared/`: shared config, constants, registry/elevation helpers.
- `src/ui/`: main window, tray icon, views, and UI helper modules.
- `tests/`: unit/integration/component/e2e test suites.
- `quality/`: release gates and quality evaluators.

## Local Commands
- Install deps: `python -m pip install -e .[dev]`
- Run tests: `pytest -q`
- Run lint: `python -m flake8 --isolated --max-line-length=120 src tests --count --statistics`
- Run release verification: `python quality/verify_release.py`
- Coverage JSON: `pytest -q --cov=src --cov-report=json:quality/reports/rescue_coverage.json`

## Quality Gates
- Full suite pass is required: `pytest -q`.
- Lint gate must include `tests`: `flake8 src tests`.
- Release checks are centralized in `quality/verify_release.py`.

## Refactoring Conventions
- Prefer helper extraction when controller/view modules grow large.
- Keep behavior-compatible changes covered by characterization tests first.
- For rescue workflow: one module surgery per session, keep blast radius small.

## Current Rescue Baseline
- Baseline autopsy artifact: `quality/reports/rescue_autopsy.json`
- Baseline rescue state: `RESCUE-STATE.md`
- Session bridge snapshot: `.rune/rescue-session-bridge.json`
