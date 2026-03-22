# Phase 3: Storage View Decomposition

## Goal
Split `StorageView` into smaller UI/controller helpers so tree rendering, filesystem actions, and scan orchestration are easier to test and no longer concentrated in one monolithic module.

## Data Flow
```text
User action -> StorageView slot
           -> scan controller / tree builder / shell action helper
           -> QTreeWidget updates or OS action
           -> status label + cached data
           -> tests assert behavior through helper seams
```

## Code Contracts
```python
# src/ui/views/storage_view_tree.py
def build_tree_item(folder_info: "FolderInfo", reference_size: int, is_root: bool = False) -> QTreeWidgetItem: ...
def add_file_entries(parent_item: QTreeWidgetItem, folder_info: "FolderInfo", reference_size: int) -> None: ...

# src/ui/views/storage_view_actions.py
def recycle_path(path: str) -> None: ...
def open_file_location(path: str) -> None: ...

# src/ui/views/storage_view.py
class StorageView(QWidget):
    def _start_realtime_scan(self, path: str) -> None: ...
    def _on_open_file_location(self, path: str) -> None: ...
    def _on_delete_item(self, path: str, item: Optional[QTreeWidgetItem] = None) -> None: ...
```

## Tasks

### Wave 1 (parallel - no dependencies)
- [ ] Task 1 - Add characterization tests around tree rendering and shell actions
  - Req: AUD-004
  - File: `tests/unit/test_storage_view_coverage.py` (modify)
  - File: `tests/unit/test_storage_view_actions.py` (new)
  - Test: these files
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_storage_view_coverage.py tests\unit\test_storage_view_actions.py -q`
  - Commit: `test(storage-view): cover tree building and shell action seams`
  - Logic: protect current behavior before decomposition.
  - Edge: protected path deletion, missing file location, root item rendering.

### Wave 2 (depends on Wave 1)
- [ ] Task 2 - Extract tree-building helpers
  - Req: AUD-004
  - depends_on: [Task 1]
  - File: `src/ui/views/storage_view_tree.py` (new)
  - File: `src/ui/views/storage_view.py` (modify)
  - Test: `tests/unit/test_storage_view_coverage.py`, `tests/unit/test_storage_view_actions.py`
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_storage_view_coverage.py tests\unit\test_storage_view_actions.py -q`
  - Commit: `refactor(storage-view): extract tree item construction helpers`
  - Logic: move `_create_tree_item` and `_add_file_entries` responsibilities into a helper module.
  - Edge: root-item formatting, percent calculations, placeholder nodes.
- [ ] Task 3 - Extract filesystem action helpers
  - Req: AUD-004
  - depends_on: [Task 1]
  - File: `src/ui/views/storage_view_actions.py` (new)
  - File: `src/ui/views/storage_view.py` (modify)
  - Test: `tests/unit/test_storage_view_actions.py` (new)
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_storage_view_actions.py -q`
  - Commit: `refactor(storage-view): isolate recycle-bin and explorer actions`
  - Logic: centralize winshell/subprocess logic and make path validation unit-testable.
  - Edge: protected paths, missing targets, Windows Explorer invocation failure.

### Wave 3 (depends on Wave 2)
- [ ] Task 4 - Shrink `StorageView` orchestration and remove dead locals/imports
  - Req: AUD-004
  - depends_on: [Task 2, Task 3]
  - File: `src/ui/views/storage_view.py` (modify)
  - File: `tests/unit/test_storage_view_coverage.py` (modify)
  - Test: `tests/unit/test_storage_view_coverage.py`, `tests/unit/test_storage_view_actions.py`
  - Verify: `..\.venv\Scripts\python.exe -m pytest tests\unit\test_storage_view_coverage.py tests\unit\test_storage_view_actions.py -q`
  - Commit: `refactor(storage-view): reduce orchestration complexity and remove dead code`
  - Logic: delegate helper work, remove unused imports/locals, and keep controller methods short.
  - Edge: scan-session sequencing, cache lookups, expanded-item behavior.

## Failure Scenarios
| When | Then | Error Type |
|------|------|-----------|
| User opens location for missing path | show info message, no crash | No fatal error |
| User deletes protected path | block action before shell call | No fatal error |
| Helper raises OS error | surface warning dialog and keep UI responsive | Recoverable UI error |
| Tree helper receives zero-size reference | render `-` or safe fallback | No fatal error |

## Performance Constraints
| Metric | Requirement | Why |
|--------|-------------|-----|
| Tree population | No extra full-tree traversal added | Large scans already stress UI |
| Complexity | `StorageView` file significantly smaller; targeted methods below radon `C` where practical | Audit closure target |

## Rejection Criteria (DO NOT)
- Do not change visible tree text/columns unless tests are updated deliberately.
- Do not move scanner logic back into UI helpers.
- Do not make helper modules depend on the whole `StorageView` instance.
- Do not keep unused imports or local variables after extraction.

## Cross-Phase Context
- Assumes Phase 2 stabilizes the scanner contract.
- Exports smaller helper modules that Phase 4 can lint independently.
- Phase 5 depends on this phase so documentation can describe the final architecture, not the legacy one.

## Acceptance Criteria
- [ ] `storage_view.py` delegates tree and shell actions to helper modules.
- [ ] New helper modules have direct unit coverage.
- [ ] Targeted StorageView tests pass.
- [ ] Unused imports/locals found in the audit are removed.
- [ ] UI behavior remains unchanged for delete/open/navigate flows.

## Traceability Matrix
| Req ID | Requirement | Task(s) | Test(s) | Status |
|--------|-------------|---------|---------|--------|
| AUD-004 | Decompose `StorageView` and reduce complexity | 1, 2, 3, 4 | `tests/unit/test_storage_view_coverage.py`, `tests/unit/test_storage_view_actions.py` | ⬚ |

## Files Touched
- `src/ui/views/storage_view.py` - modify
- `src/ui/views/storage_view_tree.py` - new
- `src/ui/views/storage_view_actions.py` - new
- `tests/unit/test_storage_view_coverage.py` - modify
- `tests/unit/test_storage_view_actions.py` - new
