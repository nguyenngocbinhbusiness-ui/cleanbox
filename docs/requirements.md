# Project Requirements

## Overview

CleanBox is a lightweight Windows desktop background app for storage monitoring and one-click directory cleanup.

---

## User Stories

### System Tray Integration
- **US-001**: As a user, I want the app to start automatically with Windows, so I don't have to remember to launch it
  - Acceptance Criteria:
    - [x] App registers in Windows startup registry
    - [x] App appears in system tray after login
  - Status: Done

- **US-005**: As a user, I want the app to run in the tray, so it doesn't clutter my taskbar
  - Acceptance Criteria:
    - [x] App has tray icon
    - [x] No taskbar button visible
  - Status: Done

- **US-006**: As a user, I want to click the tray icon to open settings, so I can easily configure the app
  - Acceptance Criteria:
    - [x] Left-click opens settings window
    - [x] Right-click shows context menu
  - Status: Done

### Storage Monitoring
- **US-002**: As a user, I want to see a notification when disk space is low, so I can take action before running out
  - Acceptance Criteria:
    - [x] Windows toast notification appears when drive < 10GB
    - [x] Notification shows drive letter and free space
    - [x] No duplicate notifications until space is freed
  - Status: Done

### Directory Cleanup
- **US-003**: As a user, I want to add folders to a cleanup list, so the app knows what to clean
  - Acceptance Criteria:
    - [x] Can add directories via Settings UI
    - [x] Directories are persisted across restarts
  - Status: Done

- **US-004**: As a user, I want one-click cleanup, so I can quickly free up space
  - Acceptance Criteria:
    - [x] "Cleanup Now" button in tray menu
    - [x] Cleans all configured directories
    - [x] Shows result notification
  - Status: Done

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-01 | Initial requirements | Antigravity Agent |
| 2026-01-02 | Marked all user stories as Done | Antigravity Agent |
