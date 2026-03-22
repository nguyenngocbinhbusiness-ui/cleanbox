# Decisions Log

## [2026-03-22 12:16] Decision: Fail Closed on Single-Instance Lock Errors

**Context:** The audit found that unrecoverable single-instance lock failures could allow duplicate background instances to start.
**Decision:** `App._acquire_single_instance()` now records a startup error and returns `False` on unrecoverable stale-lock or listen failures instead of failing open.
**Rationale:** Duplicate background instances are a correctness and user-trust problem; fail-closed behavior is safer and testable.
**Impact:** `src/app.py`, release verification, and integration coverage around startup exit behavior.

## [2026-03-22 12:16] Decision: Use One Shared Release Verification Entrypoint

**Context:** The release workflow packaged artifacts without running a consistent quality gate.
**Decision:** Local and CI release verification now flows through `quality/verify_release.py`, and the release workflow invokes that script.
**Rationale:** A single entrypoint keeps release-blocking checks aligned across developer machines and GitHub Actions.
**Impact:** `quality/verify_release.py`, `.github/workflows/release.yml`, and release-readiness verification.

## [2026-03-22 12:16] Decision: Decompose Scanner and StorageView by Helper Seams

**Context:** The audit identified `FolderScanner` and `StorageView` as the main maintainability hotspots.
**Decision:** Scanner timestamp/aggregation logic was extracted into helper seams, and StorageView tree-building plus shell actions were moved into dedicated helper modules.
**Rationale:** Smaller helpers reduce radon complexity, isolate behavior for direct tests, and keep controller methods focused on orchestration.
**Impact:** `src/features/folder_scanner/service.py`, `src/features/folder_scanner/scan_helpers.py`, `src/ui/views/storage_view.py`, `src/ui/views/storage_view_tree.py`, `src/ui/views/storage_view_actions.py`.

## [2026-03-22 12:16] Decision: Make .flake8 the Authoritative Lint Config

**Context:** Flake8 was effectively running with a 79-column baseline and conflicting expectations between local config sources.
**Decision:** Added `.flake8` as the authoritative config and aligned `pyproject.toml` to the same exclusion set.
**Rationale:** Lint cleanup is only actionable when the toolchain is reading the intended configuration.
**Impact:** `.flake8`, `pyproject.toml`, `flake8 src`, and upcoming test-lint cleanup work.
