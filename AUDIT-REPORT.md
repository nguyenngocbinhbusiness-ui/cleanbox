## Audit Report: CleanBox

- **Verdict**: WARNING
- **Overall Health**: 5.5/10
- **Total Findings**: 8 (CRITICAL: 0, HIGH: 2, MEDIUM: 6, LOW: 0)
- **Framework Checks Applied**: Python desktop app, PyQt6 UI, Windows packaging/release workflow

### Project Profile
- **Type**: Windows desktop utility
- **Runtime**: Python 3.11+ (`PyQt6`, `pystray`, `Pillow`, `win11toast`, `psutil`, `winshell`, `pywin32`)
- **Build/Release**: PyInstaller in CI, Nuitka in local helper script, NSIS installer packaging
- **Testing/Quality**: `pytest`, `bandit`, `flake8`, `compileall`, custom `quality/verify_release.py`

### Health Score
| Dimension      | Score    | Notes |
|----------------|:--------:|-------|
| Security       |   8/10   | Runtime code is mostly clean; the main confirmed issue is shell-parsed local build execution. |
| Code Quality   |   6/10   | Test coverage is strong, but exception swallowing and heavy private-attribute coupling reduce maintainability. |
| Architecture   |   5/10   | Package boundaries are weak and application orchestration is overly centralized. |
| Performance    |   6/10   | Scanner design is thoughtful, but cleanup still pays for avoidable double traversal. |
| Dependencies   |   6/10   | Dependency declarations are minimal but not reproducible enough for stable rebuilds. |
| Infrastructure |   5/10   | Release automation exists, but local/CI packaging drift and optional linting weaken confidence. |
| Documentation  |   5/10   | Supporting docs exist, but core operator documentation is still inaccurate/incomplete. |
| Mesh Analytics |   2/10   | `.rune` journaling exists, but no `.rune/metrics/` dataset was available for actual mesh analytics. |
| **Overall**    | **5.5/10** | **WARNING** |

### Phase Breakdown
| Phase          | Issues |
|----------------|--------|
| Dependencies   | 1 |
| Security       | 1 |
| Code Quality   | 2 |
| Architecture   | 1 |
| Performance    | 1 |
| Infrastructure | 2 |
| Documentation  | 1 |
| Mesh Analytics | 0 |

### Findings
1. **HIGH**: Architectural boundaries are too weak for a packaged desktop app. The published entrypoints target `main:main`, while `src/main.py` mutates `sys.path` at runtime before importing application modules, and `App` centralizes startup, tray lifecycle, config, cleanup, notification, autostart, and refresh orchestration in one object. That leaves packaging/import behavior coupled to filesystem layout and concentrates too many responsibilities in one module. Citations: `pyproject.toml:51-55`, `src/main.py:6-10`, `src/main.py:45-47`, `src/app.py:11-20`, `src/app.py:36-55`, `src/app.py:85-128`, `src/app.py:295-337`, `src/app.py:410-470`.
2. **HIGH**: Release packaging is not reproducible across environments. CI builds with PyInstaller and produces an admin installer targeting `Program Files`/`HKLM`, while the local build helper uses Nuitka and the committed `installer.nsi` targets `LOCALAPPDATA`/`HKCU`. That means local and CI release artifacts can differ in binary layout, privilege model, install path, and uninstall behavior. Citations: `.github/workflows/release.yml:37-48`, `.github/workflows/release.yml:68-97`, `build_local.py:25-59`, `build_local.py:62-99`, `installer.nsi:9-11`, `installer.nsi:42-45`.
3. **MEDIUM**: Local build execution uses shell-parsed command strings. `build_local.py` calls `subprocess.run(..., shell=True)` and later passes a composed `makensis` command string into that helper. This is a real command-injection footgun for local release tooling if any path or future argument becomes shell-significant. Citations: `build_local.py:7-12`, `build_local.py:98-99`.
4. **MEDIUM**: Broad `except Exception` handling is routine in UI orchestration and worker code, which will hide root causes and can leave partially initialized widgets/threads alive after failures. This pattern appears in constructors and interaction paths instead of being reserved for top-level crash boundaries. Citations: `src/ui/main_window.py:32-119`, `src/ui/main_window.py:131-165`, `src/ui/main_window.py:167-252`, `src/ui/views/storage_view.py:299-335`, `src/ui/tray_icon.py:36-48`, `src/ui/tray_icon.py:81-100`.
5. **MEDIUM**: Tests are heavily coupled to private implementation details, which makes refactors more expensive than they need to be. Several UI tests assert underscored widget attributes or invoke private methods directly instead of primarily validating user-observable behavior. Citations: `tests/e2e/test_ui_elements.py:63-83`, `tests/e2e/test_ui_elements.py:104-127`, `tests/e2e/test_ui_elements.py:147-153`.
6. **MEDIUM**: Cleanup still double-traverses directory trees before deletion. For directory entries, `cleanup_directory()` first computes size via `_get_dir_size()` and then immediately calls `shutil.rmtree()`, which walks the same subtree again. This is an avoidable performance hit on the core user-facing cleanup path. Citations: `src/features/cleanup/service.py:69-80`, `src/features/cleanup/service.py:144-156`.
7. **MEDIUM**: Dependency declarations are not reproducible enough for stable rebuilds. Runtime and dev requirements are expressed as lower-bound-only specifiers, and no lockfile was present at the project root during this audit. That leaves clean environments free to resolve materially different dependency sets over time. Citations: `pyproject.toml:29-49`, `requirements.txt:1-7`.
8. **MEDIUM**: Release validation under-enforces the repository’s stated quality/support contract. The workflow runs `quality/verify_release.py` without `--include-flake8`, so linting is optional in CI, and releases are only exercised on Python 3.11 even though project metadata advertises Python 3.12 and 3.13 support. Citations: `.github/workflows/release.yml:16-22`, `.github/workflows/release.yml:25-31`, `quality/verify_release.py:28-40`, `pyproject.toml:23-25`.
9. **MEDIUM**: The README documents the wrong config location. It sends operators to `%APPDATA%\CleanBox\config.json`, but the code actually stores config under `Path.home() / ".cleanbox" / "config.json"`. That creates avoidable confusion for backup, support, and manual recovery. Citations: `README.md:42-44`, `src/shared/constants.py:10-11`.

### Top Priority Actions
1. Replace the `sys.path` bootstrap with a real package entrypoint and split `App` into narrower composition/runtime services.
2. Unify local and CI release packaging so both paths produce the same installer model and artifact expectations.
3. Remove `shell=True` from `build_local.py` and pass NSIS arguments as a list.
4. Make `flake8` mandatory in `quality/verify_release.py` for CI, then either validate 3.12/3.13 in CI or narrow the advertised support matrix.
5. Remove the pre-delete size walk in `CleanupService`, or combine accounting with deletion in a single pass.
6. Fix the README config path and expand maintainer documentation for test/lint/build/release flows.

### Positive Findings
- `python -m pytest -q` passed during this audit: **564 passed** on Python `3.13.9`.
- `python quality/verify_release.py` passed, which confirms the existing release gate already covers `pytest`, `bandit`, `compileall`, and a PyInstaller smoke check. Citations: `quality/verify_release.py:30-35`, `quality/verify_release.py:44-52`.
- Destructive file operations are guarded by protected-path checks before cleanup/recycle actions are allowed. Citations: `src/features/cleanup/service.py:51-55`, `src/shared/utils.py:20-28`, `src/ui/views/storage_view_actions.py:15-27`.
- Config persistence is defensive: the app cleans stale temp files, writes via temp-and-replace, and keeps a backup file before overwrite. Citations: `src/shared/config/manager.py:48-52`, `src/shared/config/manager.py:83-104`.
- The folder scanner shows deliberate performance work already in place, including `os.scandir()` usage and parallel subdirectory scanning. Citations: `src/features/folder_scanner/service.py:249-257`, `src/features/folder_scanner/service.py:586-598`, `src/features/folder_scanner/service.py:739-760`.

### Follow-up Timeline
- Re-audit in 1 month after packaging, CI, and cleanup-path remediation.

### Verification Notes
- `python -m pytest -q`: **564 passed**
- `python quality/verify_release.py`: **passed**
- `python -m bandit -r src -f txt -ll`: **no medium/high issues**
- `python -m pip check`: reported conflicts in the active interpreter environment, but they did not map cleanly to this repo’s declared manifests and were not counted as project findings.
- `.rune/metrics/` was not present, so Mesh Analytics remained informational-only for this run.

Report saved to: `AUDIT-REPORT.md`
