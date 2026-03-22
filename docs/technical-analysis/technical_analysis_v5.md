---
document_type: technical_analysis
version: 5
version_date: 2026-03-22
author: Codex Assistant
status: active
supersedes: ./technical_analysis_v4.md
superseded_by: null
---

# Technical Analysis v5 - CleanBox

## 1. Tóm tắt kỹ thuật

CleanBox là ứng dụng desktop Windows viết bằng Python/PyQt6, kiến trúc module theo tính năng (`features`) kết hợp tầng dùng chung (`shared`) và giao diện (`ui`).

## 2. Stack hiện tại

| Thành phần | Công nghệ |
|-----------|-----------|
| Runtime | Python 3.11+ |
| UI | PyQt6 |
| Tray icon | pystray + Pillow |
| Storage metrics | psutil |
| Notification | win11toast (fallback tray) |
| Recycle Bin | winshell (+ ctypes fallback) |
| Windows integration | pywin32, winreg, schtasks |
| Packaging | PyInstaller / Nuitka + NSIS |

## 3. Kiến trúc module

```text
src/
  main.py
  app.py
  features/
    cleanup/
    folder_scanner/
    notifications/
    storage_monitor/
  shared/
    config/
    constants.py
    elevation.py
    registry.py
    utils.py
  ui/
    main_window.py
    tray_icon.py
    components/
    views/
```

## 4. Luồng xử lý chính

### 4.1 Startup
- `main.py` cấu hình logging.
- `App.start()` tạo Qt app, enforce single instance, load config.
- Khởi động `StorageMonitor`, `MainWindow`, `TrayIcon`.

### 4.2 Cleanup
- Trigger từ `CleanupView` hoặc tray.
- `App._do_cleanup()` xác nhận người dùng.
- `CleanupProgressWorker` chạy nền, emit tiến độ.
- `CleanupService` xử lý từng thư mục/Recycle Bin marker.

### 4.3 Storage scan
- `StorageView` gọi scanner qua worker riêng.
- Dữ liệu được đẩy realtime từng child để UI cập nhật dần.
- Có lazy expand cho node con và cache điều hướng.

### 4.4 Low-space monitoring
- `StorageMonitor` poll theo interval.
- Emit signal low-space, áp dụng cooldown theo drive.
- Persist danh sách drive đã thông báo trong config.

## 5. Thiết kế dữ liệu cấu hình

File: `%USERPROFILE%/.cleanbox/config.json`

Schema thực tế:
- `cleanup_directories: list[str]`
- `first_run_complete: bool`
- `low_space_threshold_gb: int`
- `polling_interval_seconds: int`
- `auto_start_enabled: bool`
- `notified_drives: dict[str, float]`

Đặc điểm triển khai:
- Atomic write (`.tmp` -> `os.replace`) + backup `.json.bak`.
- Normalize dữ liệu `notified_drives` khi load.
- Lọc đường dẫn protected trước khi lưu/đọc danh sách cleanup.

## 6. Quyết định kỹ thuật đáng chú ý

- Chạy cleanup/scan trong worker để giữ UI responsive.
- Dùng single-instance IPC nhẹ bằng `QLocalServer/QLocalSocket`.
- Áp dụng bảo vệ thao tác nguy hiểm ở nhiều lớp thay vì chỉ ở UI.
- Tối ưu scan theo hướng stream + giới hạn song song + caching.

## 7. Điểm cần cải thiện

1. Đồng bộ version hiển thị trong `SettingsView` với version thực tế.
2. Làm mới CI theo PR/branch thay vì chỉ release tag.
3. Bổ sung lock/constraints cho dependency để tăng reproducibility.
