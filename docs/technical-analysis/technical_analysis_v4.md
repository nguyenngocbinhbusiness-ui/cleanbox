---
# DOCUMENT METADATA
document_type: technical_analysis
version: 4
version_date: 2026-01-04
author: Antigravity Agent
status: draft
supersedes: ./technical_analysis_v3.md
superseded_by: null

# VERSION METADATA
change_summary: "Added CleanupProgressWorker architecture for progress indicator feature"
change_type: minor
reviewed_by: null
review_date: null

# PROJECT METADATA
project_name: CleanBox - Storage Monitor & Cleanup App
feature_name: Cleanup Progress Indicator
related_documents:
  - path: ../business-analysis/business_analysis_v4.md
    relationship: companion
---

# Technical Analysis v4

## Tech Stack Registry

| Technology | Version | Purpose | Projects Using |
|------------|---------|---------|----------------|
| Python | 3.11+ | Runtime | CleanBox |
| PyQt6 | 6.6+ | GUI Framework | CleanBox |
| pystray | 0.19+ | System Tray | CleanBox |
| win10toast-click | 0.1+ | Windows Notifications | CleanBox |
| psutil | 5.9+ | System Monitoring | CleanBox |
| winshell | 0.6+ | Recycle Bin access | CleanBox |
| pywin32 | 306+ | Windows COM/Registry | CleanBox |

## Projects/Features Analyzed

### CleanBox - Cleanup Progress Indicator
- **Date**: 2026-01-04
- **Status**: Active

---

## Technical Overview

CleanBox is a lightweight Windows desktop application built with Python and PyQt6. Uses **feature-based folder structure** per `.agent/standards/folder-structure.md`.

**Key Updates in v4**:
- **CleanupProgressWorker**: New QThread-based worker for non-blocking cleanup with progress signals.
- **UI Progress**: QProgressBar in CleanupView for visual feedback.
- **Tray Status**: Dynamic tooltip update during cleanup.

---

## App Category

| Category | Value |
|----------|-------|
| **Type** | Desktop |
| **Platform** | Windows 10/11 |
| **Architecture** | Monolith (single executable) |

---

## Tech Stacks

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| Runtime | Python | 3.11+ | User preference, `.venv` exists |
| GUI Framework | PyQt6 | 6.6+ | User choice, modern Qt bindings |
| Threading | PyQt6.QThread | 6.6+ | Thread-safe progress signals |
| System Tray | pystray | 0.19+ | Cross-platform, lightweight |
| Notifications | win10toast-click | 0.1+ | Native Windows toasts |
| System Info | psutil | 5.9+ | Disk monitoring |
| Recycle Bin | winshell | 0.6+ | Empty Recycle Bin API |
| Windows API | pywin32 | 306+ | Registry, COM support |

---

## Dependencies

| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| PyQt6 | >=6.6.0 | GUI framework | GPL/Commercial |
| pystray | >=0.19.0 | System tray icon | LGPL |
| Pillow | >=10.0.0 | Icon image handling | HPND |
| win10toast-click | >=0.1.0 | Windows notifications | MIT |
| psutil | >=5.9.0 | Disk space monitoring | BSD |
| winshell | >=0.6 | Recycle Bin operations | MIT |
| pywin32 | >=306 | Windows API access | PSF |

---

## System Requirements

| Requirement | Specification |
|-------------|---------------|
| **OS** | Windows 10/11 |
| **Python** | 3.11+ |
| **Memory** | < 50MB RAM (NFR-001) |
| **CPU** | < 1% average (NFR-002) |

---

## Module Architecture (Feature-Based)

```
project/src/
├── features/
│   ├── storage_monitor/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── utils.py
│   │
│   ├── cleanup/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── directory_detector.py
│   │   └── worker.py           # NEW: CleanupProgressWorker
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── service.py
│   │
│   └── settings/
│       ├── __init__.py
│       └── window.py
│
├── shared/
│   ├── config/
│   ├── constants.py
│   └── registry.py
│
├── ui/
│   ├── components/
│   │   ├── sidebar.py
│   │   └── content_panel.py
│   ├── views/
│   │   └── cleanup_view.py     # MODIFIED: + QProgressBar
│   ├── main_window.py          # MODIFIED: Forward progress methods
│   └── tray_icon.py            # MODIFIED: + set_status()
│
├── app.py                      # MODIFIED: Use CleanupProgressWorker
└── main.py
```

---

## Detailed Design: Cleanup Progress Feature

### CleanupProgressWorker

**Purpose**: Run cleanup in background thread with progress signals.

**Signal Flow**:
```
CleanupProgressWorker (QThread)
    ├── progress_updated(int, int)  → current directory index, total count
    └── cleanup_finished(object)    → CleanupResult with totals
```

**Implementation**:
```python
class CleanupProgressWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    cleanup_finished = pyqtSignal(object)
    
    def __init__(self, directories: List[str], parent=None):
        super().__init__(parent)
        self._directories = directories
        self._service = CleanupService()
    
    def run(self):
        total = len(self._directories)
        result = CleanupResult()
        
        for i, directory in enumerate(self._directories):
            self.progress_updated.emit(i, total)
            dir_result = self._cleanup_one(directory)
            self._accumulate(result, dir_result)
        
        self.progress_updated.emit(total, total)
        self.cleanup_finished.emit(result)
```

### UI Progress Bar

**Component**: `QProgressBar` in CleanupView
- Hidden by default
- Shows during cleanup
- Style: Modern flat design with brand color

### Tray Status Update

**API**: `TrayIcon.set_status(text: Optional[str])`
- Updates `_icon.title` (tooltip)
- `None` resets to default app name

---

## Integration Points

| Integration | Type | Details | Auth |
|-------------|------|---------|------|
| Windows Registry | System API | `HKCU\...\Run` for auto-start | None |
| Windows Notifications | Toast API | win10toast-click | None |
| Recycle Bin | Shell API | winshell.recycle_bin() | None |
| File System | OS API | Read/Delete directories | User perms |

---

## Technical NFRs

| Metric | Requirement | Priority |
|--------|-------------|----------|
| Memory Usage | < 50MB RAM | High |
| CPU Usage | < 1% average | High |
| Startup Time | < 3 seconds | Medium |
| Portability | Works on any Windows user | High |
| **UI Responsiveness** | **UI must not freeze during cleanup (use QThread)** | **High** |
