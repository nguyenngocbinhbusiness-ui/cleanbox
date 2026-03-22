# CleanBox

Windows-only desktop utility for storage monitoring, folder analysis, and one-click cleanup.

## Quick Start

Requirements:
- Windows 10 or Windows 11
- Python 3.11+

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python src/main.py
```

After launch, CleanBox creates a single-instance tray app, shows the main window, seeds default cleanup targets on first run, and starts polling local drives for low-space warnings.

## Features

- System tray integration with `Cleanup Now`, `Settings`, and `Exit` actions
- First-run setup that adds the current user's `Downloads` folder and the Windows Recycle Bin to the cleanup target list
- Cleanup workflow with confirmation dialog, background progress worker, and completion notifications
- Storage monitor with low-space notifications, per-drive cooldowns, and periodic maintenance
- Storage Analyzer view for drive scanning, real-time folder results, lazy expansion, cached navigation, and context-menu actions
- Protected-path safeguards that block cleanup or deletion of critical system locations
- Auto-start support via Windows Registry, with a Task Scheduler fallback when registry writes fail
- Restart-with-admin action when CleanBox is running without elevation

## Tech Stack

- Python 3.11+
- PyQt6 for the desktop UI and event loop
- `pystray` + Pillow for system tray integration
- `psutil` for drive and process metrics
- `winshell` and Win32 APIs for Recycle Bin and Windows shell operations
- `win11toast` for toast notifications with tray fallback
- PyInstaller and NSIS in the release pipeline

## Project Structure

- `src/main.py`: process entry point and logging bootstrap
- `src/app.py`: application orchestrator, single-instance lock, service wiring, and lifecycle
- `src/features/cleanup/`: cleanup service, worker, and default-directory detection
- `src/features/folder_scanner/`: TreeSize-style folder scanning and scan helpers
- `src/features/storage_monitor/`: drive polling and low-space detection
- `src/features/notifications/`: toast and tray fallback notifications
- `src/shared/`: configuration, constants, elevation, registry, and shared utilities
- `src/ui/`: main window, tray integration, and view components
- `tests/`: unit, component, integration, UI, and end-to-end coverage
- `quality/`: release verification and quality reporting helpers
- `docs/requirements.md`: user stories and acceptance criteria

## Configuration

CleanBox stores configuration in `%USERPROFILE%\.cleanbox\config.json`.

Current persisted keys from `ConfigManager`:
- `cleanup_directories`
- `first_run_complete`
- `low_space_threshold_gb`
- `polling_interval_seconds`
- `auto_start_enabled`
- `notified_drives`

Behavior enforced by the current code:
- First launch populates cleanup targets with `Downloads` and the Recycle Bin marker
- Protected system paths are filtered out when loading or adding cleanup directories
- Config writes use an atomic temporary file with backup recovery fallback
- Log output is written to `%USERPROFILE%\.cleanbox\cleanbox.log`

## Development

```powershell
pytest
python -m flake8 src tests
python quality/verify_release.py
python build_local.py
```

Notes:
- `pytest` uses the settings in `pyproject.toml`
- `build_local.py` builds local Windows artifacts with Nuitka and optionally NSIS
- `.github/workflows/release.yml` builds tagged Windows releases with PyInstaller and NSIS

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the runtime model, module map, and main data flows.

## API Reference

CleanBox does not expose an HTTP or RPC API. It is a local Windows desktop application.

## License

MIT
