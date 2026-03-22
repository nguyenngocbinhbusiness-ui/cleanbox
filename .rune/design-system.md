# CleanBox Design System

## Product Context
- Platform: Windows desktop utility (PyQt6)
- Primary use: disk cleanup and storage monitoring
- UX goal: fast, clear, and safe cleanup actions

## Design Principles
- Clarity first: prioritize readability and status visibility
- Safety-first actions: highlight destructive actions and confirmations
- Low-noise UI: focus on information hierarchy over decoration

## Visual Direction
- Theme: neutral, system-friendly desktop UI
- Surface contrast: high enough for long-running utility use
- Color semantics:
  - Primary: app actions and active controls
  - Success: completed cleanups and healthy storage states
  - Warning: low disk space and risky actions
  - Danger: irreversible/destructive operations

## Typography
- Follow platform-default sans serif for native consistency
- Use larger weight/size for section headers and disk status summaries

## Components
- Main navigation sidebar
- Storage status cards and usage bars
- Cleanup directory list with validation states
- Confirmation dialogs for cleanup/delete operations
- Toast/tray notifications for background events

## Motion and Feedback
- Keep transitions subtle and short
- Always provide progress feedback for background cleanup tasks
- Ensure action confirmations are explicit for destructive operations

## Accessibility
- Keyboard-accessible primary actions and dialogs
- Sufficient contrast on status colors
- Do not rely on color alone for warning/danger states
