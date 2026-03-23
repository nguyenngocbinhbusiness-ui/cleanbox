# Rescue Autopsy Report

- Health score: **53.77 / 100**
- Modules analyzed: **14**

## Weakest Modules

| Module | LOC | Max CC | Coverage | Health | Pattern |
|---|---:|---:|---:|---:|---|
| ui.views | 2283 | 17 | 68.61% | 40.24 | Strangler Fig |
| shared | 783 | 12 | 77.66% | 49.28 | Strangler Fig |
| features.folder_scanner | 851 | 13 | 79.47% | 55.5 | Strangler Fig |
| app | 508 | 11 | 75.16% | 62.56 | Extract & Simplify |
| features.cleanup | 309 | 13 | 81.79% | 66.94 | Extract & Simplify |
| features.storage_monitor | 254 | 8 | 81.46% | 75.29 | Branch by Abstraction |
| ui.main_window.py | 258 | 4 | 73.68% | 76.94 | Expand-Migrate-Contract |
| ui.components | 119 | 4 | 73.91% | 79.65 | Expand-Migrate-Contract |

## Top Issues

- [MEDIUM] src/shared/elevation.py: Low coverage: 40.00%
- [LOW] src/shared/config/manager.py: Low coverage: 60.00%
- [LOW] src/shared/elevation.py: B404 at line 6: Consider possible security implications associated with the subprocess module.
- [LOW] src/shared/registry.py: B404 at line 6: Consider possible security implications associated with the subprocess module.
- [LOW] src/shared/registry.py: B603 at line 55: subprocess call - check for execution of untrusted input.
- [LOW] src/shared/registry.py: B603 at line 67: subprocess call - check for execution of untrusted input.
- [LOW] src/ui/views/storage_view.py: Low coverage: 60.24%
- [LOW] src/ui/views/storage_view_actions.py: B606 at line 51: Starting a process without a shell.
