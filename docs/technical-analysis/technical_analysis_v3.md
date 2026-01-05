---
# DOCUMENT METADATA
document_type: technical_analysis
version: 3
version_date: 2026-01-02
author: Antigravity Agent
status: draft
supersedes: ./technical_analysis_v2.md
superseded_by: null

# VERSION METADATA
change_summary: "Updated UI architecture to support Sidebar+Content layout (QSplitter/QHBoxLayout)"
change_type: minor
reviewed_by: null
review_date: null

# PROJECT METADATA
project_name: CleanBox - Storage Monitor & Cleanup App
feature_name: Initial Release
related_documents:
  - path: ../business-analysis/business_analysis_v3.md
    relationship: companion
---

# Technical Analysis v3

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
UI will leverage **PyQt6 Layouts** to implement a "Sidebar + Content" Split View pattern.

**Key Updates in v3**:
- **UI Architecture**: Defined clear SplitView implementation strategy.
- Styles: Usage of QSS (Qt Style Sheets) to match specific visual requirements (padding, colors).

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
│   ├── storage_monitor/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── utils.py
│   │
│   ├── cleanup/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── directory_detector.py
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── service.py
│   │
│   └── settings/
│       ├── __init__.py
│       └── window.py         # Main UI Window (Split View)
│
├── shared/
│   ├── config/
│   ├── constants.py
│   └── registry.py
│
├── ui/
│   ├── components/           # NEW: Reusable UI components
│   │   ├── sidebar.py        # Sidebar navigation widget
│   │   └── content_panel.py  # Right-side content area
│   └── tray_icon.py
│
├── app.py
└── main.py
```

---

## Details Design: UI Layout

### Split View Pattern
- **Component**: `QWidget` with `QHBoxLayout`.
- **Left**: `SidebarWidget` (Custom `QFrame` or `QListWidget`).
    - Fixed width or typically 25%.
    - Background: Light gray / White.
    - Styling: List items with icons.
- **Right**: `QStackedWidget` or `ContentPanel`.
    - Dynamic content based on sidebar selection.
    - Views:
        - "Drives/Storage" (Default).
        - "Cleanup Targets" (List of folders).
        - "Settings".

### Visual Integration
- **Icons**: Use standard SVGs (Heroicons/Lucide adapted for Desktop if possible, or standard QStyleStandardPixmap).
- **Style**:
    - Clean padding (16px+).
    - Rounded buttons.
    - Progress bars for disk usage.

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
