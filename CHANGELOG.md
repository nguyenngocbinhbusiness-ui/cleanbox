# Changelog

## [1.0.18] - 2026-03-20

### Added
- Scan completeness accounting (`scanned_files`, `scanned_dirs`, skip counters and reasons) for folder scanning results.
- Session isolation for real-time scan UI updates to ignore stale worker signals after cancel/restart.
- Regression tests for scan stats aggregation and stale-session signal handling.

### Changed
- Scanner now streams `os.scandir()` entries instead of materializing full lists, reducing memory spikes on large folders.
- Parallel scanner worker count is adaptive by CPU and configurable via `CLEANBOX_SCANNER_WORKERS`.
- Realtime completion status text now includes completeness counters when available.

### Fixed
- Cancel flow now invalidates active scan session and clears pending buffered child updates.
- Unit tests stabilized by removing modal-dialog side effects and aligning main-entry mocks with admin path.

---

## [1.0.17] - 2026-01-09

### Fixed
- **ROOT CAUSE FIXED**: Python 3.11 compatibility for f-strings
- Multi-line f-strings (PEP 701, Python 3.12+) converted to single-line
- Files fixed: `notifications/service.py`, `storage_view.py`
- ✅ **Local build verified working**

---

## [1.0.16] - 2026-01-09

## [1.0.14] - 2026-01-09

## [1.0.12] - 2026-01-09

## [1.0.10] - 2026-01-08

---

## [1.0.9] - 2026-01-08

### Fixed
- Fixed build: assets now bundled correctly via `--add-data` flag
- Application icon and resources now work in release builds

---

## [1.0.8] - 2026-01-08

### Fixed
- Fixed release workflow (Windows-only app, not cross-platform)
- Improved artifact packaging with proper version naming

---

## [1.0.7] - 2026-01-08

### Changed
- Enhanced GitHub Actions release workflow
- Improved artifact naming with version prefix
- Added automatic release notes generation

---

## [1.0.6] - 2026-01-08

### Added
- Added application icon (`icon.ico`)
- New unit tests for constants module
- Comprehensive registry tests

### Changed
- Improved app.py functionality
- Enhanced constants configuration

---

## [1.0.5] - 2026-01-06

### Changed
- New release build with icon improvements
- Synced all pending changes

---

## [1.0.3] - 2026-01-06

### Changed
- Patch release with stability improvements

---

## [1.0.2] - 2026-01-06

### Changed
- Cleaned up workflow configuration
- Fixed import ordering in main module
- Removed unused Dockerfile

---

## [1.0.1] - 2026-01-05

### Changed
- Added GitHub Actions workflow for automated releases

---

## [1.0.0] - 2024-06-01

### Added
- Initial release of CleanBox.
- Disk cleanup utility with system tray support.
