# Conventions

## [2026-03-22] Convention: Shared Verification Entrypoint

**Pattern:** Release-blocking quality checks should be defined once in `quality/verify_release.py` and reused by CI instead of duplicating commands in workflows.
**Example:** `.github/workflows/release.yml` runs `python quality/verify_release.py`.
**Applies to:** Release workflows, local pre-release verification, and future quality gate expansion.

## [2026-03-22] Convention: Helper Extraction Before UI Controller Growth

**Pattern:** When a view/controller accumulates rendering or shell-action logic, extract pure or low-dependency helpers into sibling modules and keep the view as orchestration only.
**Example:** `storage_view.py` delegates to `storage_view_tree.py` and `storage_view_actions.py`.
**Applies to:** `src/ui/views/*` and similar controller-heavy modules.

## [2026-03-22] Convention: Scanner Failures Must Be Accounted For Explicitly

**Pattern:** Scanner paths should record skip reasons or parse failures instead of swallowing exceptions silently.
**Example:** malformed folder timestamps now record `mtime_parse_error` through `ScanStats`.
**Applies to:** `src/features/folder_scanner/*` and future filesystem traversal code.
