# Phase 2: Scanner Core Simplification

## Goal
Reduce `FolderScanner` complexity, remove silent exception swallowing, and make scan failure accounting explicit without regressing realtime scan behavior.

## Data Flow
```text
StorageView -> FolderScanner.scan_children_realtime()
           -> scandir iteration -> file/dir processing
           -> helper merge + timestamp parse + skip accounting
           -> FolderInfo + ScanStats
           -> UI callbacks / cached results
```

## Code Contracts
```python
# src/features/folder_scanner/scan_helpers.py
def parse_last_modified(value: str) -> float | None: ...
def merge_child_folder(
    *,
    child_info: "FolderInfo",
    total_size: int,
    total_allocated: int,
    file_count: int,
    folder_count: int,
    max_mtime: float,
) -> tuple[int, int, int, int, float]: ...

# src/features/folder_scanner/service.py
class FolderScanner:
    def scan_children_realtime(
        self,
        path: str,
        child_callback: Callable[["FolderInfo"], None],
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Optional["FolderInfo"]: ...
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Add characterization tests for skip accounting and realtime merges
  - Req: AUD-003
  - File: `tests/unit/test_folder_scanner_coverage.py` (modify)
  - File: `tests/unit/test_features_scanner.py` (modify)
  - File: `tests/unit/test_folder_scanner_realtime.py` (new)
  - Test: these files
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_folder_scanner_coverage.py tests\unit\test_features_scanner.py tests\unit\test_folder_scanner_realtime.py -q`
  - Commit: `test(scanner): lock down realtime scan merge and error accounting behavior`
  - Logic: capture current good behavior before refactor.
  - Edge: malformed date strings, inaccessible directories, cancellation mid-scan.
- [ ] Task 2 - Extract deterministic helper functions
  - Req: AUD-003
  - File: `src/features/folder_scanner/scan_helpers.py` (new)
  - File: `src/features/folder_scanner/__init__.py` (modify if exports are needed)
  - Test: `tests/unit/test_folder_scanner_realtime.py` (new)
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_folder_scanner_realtime.py -q`
  - Commit: `refactor(scanner): extract timestamp and aggregate helpers`
  - Logic: isolate date parsing and child-stat merge logic from the main service body.
  - Edge: empty timestamp, invalid timestamp, zero-byte children.

### Wave 2 (depends on Wave 1)
- [ ] Task 3 - Replace silent `except/pass` with tracked outcomes
  - Req: AUD-003
  - depends_on: [Task 1, Task 2]
  - File: `src/features/folder_scanner/service.py` (modify)
  - Test: `tests/unit/test_folder_scanner_coverage.py`, `tests/unit/test_folder_scanner_realtime.py`
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_folder_scanner_coverage.py tests\unit\test_folder_scanner_realtime.py -q`
  - Commit: `fix(scanner): track realtime metadata parse failures instead of swallowing them`
  - Logic: replace `except Exception: pass` with helper-driven accounting and debug logging.
  - Edge: partial child results, callback exceptions, nested permission errors.

### Wave 3 (depends on Wave 2)
- [ ] Task 4 - Break complex scan branches into smaller private helpers
  - Req: AUD-003
  - depends_on: [Task 3]
  - File: `src/features/folder_scanner/service.py` (modify)
  - File: `tests/unit/test_features_scanner.py` (modify)
  - Test: `tests/unit/test_folder_scanner_coverage.py`, `tests/unit/test_features_scanner.py`, `tests/unit/test_folder_scanner_realtime.py`
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_folder_scanner_coverage.py tests\unit\test_features_scanner.py tests\unit\test_folder_scanner_realtime.py -q`
  - Commit: `refactor(scanner): split realtime and recursive scan branches into smaller helpers`
  - Logic: extract helper methods until radon no longer reports `D` complexity for the targeted methods.
  - Edge: preserving cancellation semantics, preserving callback order, preserving `ScanStats.merge`.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| `last_modified` is malformed | record skip reason and continue | No fatal error |
| Child scan raises `PermissionError` | skip child, increment skip stats, continue | Recoverable scan condition |
| Cancellation flag is set mid-scan | return `None` or partial result per current contract | No exception |
| Helper extraction changes counts | tests fail; do not ship | Regression |

## Performance Constraints
| Metric | Requirement | Why |
|--------|-------------|-----|
| Realtime scan throughput | No slower than current tests by >10% | Refactor must not erase scan gains |
| Complexity | No `D` grades for `scan_children_realtime` or `_scan_recursive` | Audit closure target |

## Rejection Criteria (DO NOT)
- Do not change `FolderInfo` or `ScanStats` public shape without updating all callers.
- Do not replace explicit skip accounting with generic logging only.
- Do not add new scan passes over the filesystem just to reduce complexity.
- Do not refactor `StorageView` in this phase; keep UI changes out.

## Cross-Phase Context
- Assumes Phase 1 kept test execution reliable and available for fast iteration.
- Exports a cleaner scanner API and more predictable skip accounting for Phase 3.
- Phase 3 depends on scanner contracts staying stable while UI code is decomposed.

## Acceptance Criteria
- [ ] Silent `except/pass` is removed from realtime merge logic.
- [ ] Targeted scanner methods drop below radon `D` complexity.
- [ ] Realtime and recursive scan tests pass.
- [ ] Skip reasons remain observable via `ScanStats`.
- [ ] No regression in cancellation or callback order.

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-003 | Reduce scanner complexity and remove silent failure handling | 1, 2, 3, 4 | `tests/unit/test_folder_scanner_coverage.py`, `tests/unit/test_features_scanner.py`, `tests/unit/test_folder_scanner_realtime.py` | ⬚ |

## Files Touched
- `src/features/folder_scanner/service.py` - modify
- `src/features/folder_scanner/scan_helpers.py` - new
- `src/features/folder_scanner/__init__.py` - modify if needed
- `tests/unit/test_folder_scanner_coverage.py` - modify
- `tests/unit/test_features_scanner.py` - modify
- `tests/unit/test_folder_scanner_realtime.py` - new
