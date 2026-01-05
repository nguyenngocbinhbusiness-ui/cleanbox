---
# DOCUMENT METADATA
document_type: technical_analysis
version: 2
version_date: 2026-01-02
author: Antigravity Agent
status: draft
supersedes: ./technical_analysis_v1.md
superseded_by: null

# VERSION METADATA
change_summary: "Updated folder structure to feature-based layout, added winshell/pywin32 for Recycle Bin, added directory_detector module"
change_type: minor
reviewed_by: null
review_date: null

# PROJECT METADATA
project_name: CleanBox - Storage Monitor & Cleanup App
feature_name: Initial Release
related_documents:
  - path: ../business-analysis/business_analysis_v2.md
    relationship: companion
---

# Technical Analysis v2

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

### CleanBox - Storage Monitor & Cleanup App
- **Date**: 2026-01-02
- **Status**: Active

---

## Technical Overview

CleanBox is a lightweight Windows desktop application built with Python and PyQt6. Uses **feature-based folder structure** per `.agent/standards/folder-structure.md`.

**Key Updates in v2**:
- Feature-based module organization
- Auto-detect default directories (Downloads + Recycle Bin)
- winshell/pywin32 for Recycle Bin operations

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
│   ├── storage_monitor/      # US-002: Low space detection
│   │   ├── __init__.py
│   │   ├── service.py        # StorageMonitor class
│   │   └── utils.py          # Drive helpers
│   │
│   ├── cleanup/              # US-004: One-click cleanup
│   │   ├── __init__.py
│   │   ├── service.py        # CleanupService class
│   │   └── directory_detector.py  # BR-005: Auto-detect defaults
│   │
│   ├── notifications/        # Toast notifications
│   │   ├── __init__.py
│   │   └── service.py
│   │
│   └── settings/             # US-006: Settings UI
│       ├── __init__.py
│       └── window.py
│
├── shared/
│   ├── config/
│   │   ├── __init__.py
│   │   └── manager.py        # JSON config
│   ├── constants.py
│   └── registry.py           # US-001: Auto-start
│
├── ui/
│   └── tray_icon.py          # US-005: System tray
│
├── app.py
└── main.py
```

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
