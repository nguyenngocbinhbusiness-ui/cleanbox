# API nội bộ CleanBox

## Phạm vi API

CleanBox **không cung cấp HTTP API public** hoặc RPC endpoint cho mạng ngoài.

Ứng dụng là desktop app cục bộ; các tương tác chính gồm:
- Signal/slot nội bộ giữa các thành phần PyQt6.
- Tích hợp API hệ điều hành Windows (Registry, Shell, Recycle Bin, tray/notification).

## Bề mặt tích hợp chính

| Thành phần | Mô tả |
|-----------|-------|
| `StorageMonitor` signals | `low_space_detected(DriveInfo)`, `low_space_cleared(str)` |
| `CleanupProgressWorker` signals | `progress_updated(int, int)`, `cleanup_finished(object)` |
| `MainWindow` signals | `directory_added`, `directory_removed`, `cleanup_requested`, `autostart_changed`, `threshold_changed`, `interval_changed` |

## Ghi chú

Nếu sau này cần tích hợp từ ứng dụng khác (CLI/service), nên tạo lớp API riêng thay vì gọi trực tiếp vào UI layer.
