# Rescue Autopsy Report

- Health score: **81.81 / 100**
- Modules analyzed: **51**

## Weakest Modules

| Module | LOC | Max CC | Coverage | Issues | Health | Pattern |
|---|---:|---:|---:|---:|---:|---|
| shared.config | 312 | 8 | 82.78% | 0 | 74.65 | Branch by Abstraction |
| ui.storage.tree_engine | 223 | 8 | 80.00% | 0 | 74.74 | Branch by Abstraction |
| features.folder_scanner.service | 550 | 8 | 91.63% | 0 | 75.19 | Strangler Fig |
| ui.storage.storage_view_expand | 108 | 9 | 80.26% | 0 | 75.50 | Branch by Abstraction |
| ui.views.cleanup_view | 251 | 6 | 77.61% | 0 | 75.95 | Expand-Migrate-Contract |
| ui.main_window.py | 258 | 4 | 73.68% | 0 | 76.69 | Expand-Migrate-Contract |
| features.folder_scanner.size_walker | 53 | 13 | 91.89% | 0 | 76.92 | Extract & Simplify |
| features.folder_scanner.recursive_engine | 203 | 10 | 89.04% | 0 | 77.13 | Branch by Abstraction |
