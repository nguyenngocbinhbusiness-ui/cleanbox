## Audit Report: CleanBox

- **Verdict**: WARNING
- **Overall Health**: 6.6/10
- **Total Findings**: 5 (CRITICAL: 0, HIGH: 1, MEDIUM: 3, LOW: 1)
- **Framework Checks Applied**: Python desktop app, PyQt6, Windows-specific packaging/registry checks

### Health Score
| Dimension      | Score    | Notes              |
|----------------|:--------:|--------------------|
| Security       |   8/10   | No high-confidence security flaws found; bandit and protected-path guardrails are in place. |
| Code Quality   |   7/10   | Strong test coverage, but some UI/state paths are inconsistent. |
| Architecture   |   6/10   | Clear module split, but one settings flow is wired only at the view layer. |
| Performance    |   6/10   | Scanner architecture is thoughtful, but a few UI and cleanup paths still block or double-scan. |
| Dependencies   |   5/10   | Dependency surface is small, but version policy is too loose for reproducible builds. |
| Infrastructure |   7/10   | Release automation exists and passes, but CI is release-only and lint is optional. |
| Documentation  |   8/10   | README and architecture docs are solid; one shipped version string is stale. |
| Mesh Analytics |   3/10   | `.rune` journal data exists, but no `.rune/metrics/` telemetry was present. |
| **Overall**    | **6.6/10** | **WARNING**      |

### Phase Breakdown
| Phase          | Issues |
|----------------|--------|
| Dependencies   | 1      |
| Security       | 0      |
| Code Quality   | 1      |
| Architecture   | 1      |
| Performance    | 2      |
| Infrastructure | 1      |
| Documentation  | 1      |
| Mesh Analytics | 1      |

### Top Priority Actions
1. Wire the Settings monitoring controls into persistence and `StorageMonitor` updates so threshold and polling changes actually take effect. `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:22`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:239`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\app.py:100`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\shared\config\manager.py:195`
2. Remove the 2-second blocking wait from expand-scan cancellation on the GUI thread. `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\storage_view.py:1103`
3. Stop pre-walking directories just to measure cleanup size before deletion; it doubles filesystem work on large folders. `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:77`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:144`

### Findings

#### HIGH
- **Storage monitoring settings are dead UI controls.**
  `SettingsView` emits `threshold_changed` and `interval_changed`, and the spinboxes are wired locally, but `MainWindow` does not expose matching signals and `App` never connects handlers for them. `ConfigManager` also has getters only, with no setters for either field. As shipped, users can change the controls without affecting persisted config or the live `StorageMonitor`. This is a real behavior gap, not just a docs issue.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:22`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:130`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:146`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:239`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\app.py:100`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\shared\config\manager.py:195`

#### MEDIUM
- **Expand-scan cancellation can freeze the UI for up to 2 seconds.**
  When a user expands a second tree node while a prior expand scan is still running, the view cancels the worker and then calls `wait(2000)` on the GUI thread. That creates an avoidable visible stall exactly in the interactive path the feature is trying to optimize.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\storage_view.py:1099`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\storage_view.py:1107`

- **Directory cleanup does a full size walk before deleting each folder.**
  For every subdirectory, `cleanup_directory()` calls `_get_dir_size()` and then immediately runs `shutil.rmtree()`. On large folders this doubles I/O and can substantially inflate cleanup latency with no correctness benefit beyond reporting an approximate freed size.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:76`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:77`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:78`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:144`

- **Dependency policy is not reproducible enough for reliable auditing.**
  Both `pyproject.toml` and `requirements.txt` specify only open-ended minimum versions, and the repo has no lockfile or constraints file. That makes the installed dependency graph vary over time, which weakens vulnerability triage and makes release/debug parity harder.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\pyproject.toml:29`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\pyproject.toml:40`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\requirements.txt:1`

- **CI protection is limited to release tags and skips lint unless someone opts in locally.**
  The only GitHub Actions workflow runs on `push` tags matching `v*`, so ordinary branch and PR changes are not gated in CI. The shared `verify_release.py` helper supports flake8 only behind `--include-flake8`, and the workflow does not pass that flag.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\.github\workflows\release.yml:3`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\.github\workflows\release.yml:31`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\quality\verify_release.py:28`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\quality\verify_release.py:36`

#### LOW
- **User-facing version text is stale.**
  The settings footer still renders `CleanBox v1.0.0`, while package metadata reports `1.0.18`. That is a small issue, but it undermines release supportability because screenshots and bug reports can reflect the wrong version.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\settings_view.py:157`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\pyproject.toml:7`

### Positive Findings
- The project’s own release gate passed locally: `python quality/verify_release.py` completed successfully, including `pytest`, `bandit`, `compileall`, and a PyInstaller smoke check.
- Test coverage breadth is strong for a desktop app: the repo currently ships 564 passing tests across unit, component, integration, UI, and e2e suites. Evidence: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\tests`
- Destructive-path safety is enforced in multiple layers, not just one. Protected path checks appear in cleanup execution, config persistence, and storage-view actions. Evidence: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\cleanup\service.py:51`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\shared\config\manager.py:126`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\storage_view_actions.py:17`
- The storage analyzer already uses sensible performance primitives: `os.scandir()`, bounded worker counts, and a capped navigation cache. Evidence: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\folder_scanner\service.py:157`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\features\folder_scanner\service.py:179`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\src\ui\views\storage_view.py:927`

### Phase Notes
- **Phase 0: Discovery**
  Project profile: Python 3.11+ Windows desktop application with PyQt6 UI, `pystray` tray integration, `psutil` for storage metrics, and PyInstaller/NSIS packaging. Applicable checks: Python desktop, Windows registry/task scheduler, packaging/release pipeline.

- **Phase 1: Dependencies**
  No high-confidence CVE finding was provable from local files alone, but dependency hygiene is weakened by floating minimum-only specs and no lockfile.  
  Citations: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\pyproject.toml:29`, `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\requirements.txt:1`

- **Phase 2: Security**
  No >80% confidence security defect was found in local review. `bandit -r src -f txt -ll` returned no reportable issues, and the codebase consistently applies protected-path checks before destructive filesystem operations.

- **Phase 3: Code Quality**
  Functional quality is supported by the passing 564-test suite, but the stale version string and dead monitoring settings show that some product-facing wiring drifted away from the intended architecture.

- **Phase 4: Architecture**
  The module map is mostly clean (`features/`, `shared/`, `ui/`), but the monitoring settings path breaks the layering contract: the view exposes behavior the application core never consumes.

- **Phase 5: Performance**
  Scanner design is generally strong, but the UI-thread wait and cleanup double-walk are concrete hotspots that should be removed first.

- **Phase 6: Infrastructure**
  Release automation is present and useful, but it acts as a release pipeline rather than a general CI gate. There is no evidence of PR-time workflow coverage in the audited repo.

- **Phase 7: Documentation**
  README and `ARCHITECTURE.md` are both useful and current overall. The main mismatch is the stale version shown in the settings UI versus package metadata.

- **Phase 8: Mesh Analytics**
  `.rune/metrics/` was not present, so mesh analytics could not be computed. `.rune/journal/` and other planning artifacts do exist, which suggests process discipline without telemetry.  
  INFO: No metrics data yet — run a few instrumented cook sessions first.

### Follow-up Timeline
- Re-audit in 1 month after fixing the settings wiring and the two performance-path issues.

Report saved to: `D:\SOFTWARE\LOCAL_APP\CLEANBOX\project\AUDIT-REPORT.md`
