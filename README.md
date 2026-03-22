# CleanBox

Ứng dụng desktop Windows (PyQt6) giúp theo dõi dung lượng ổ đĩa, phân tích thư mục theo kiểu TreeSize và dọn dẹp nhanh các thư mục đã cấu hình.

## Bắt đầu nhanh

Yêu cầu:
- Windows 10/11
- Python 3.11+

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python src/main.py
```

Khi chạy từ source, ứng dụng sẽ:
- Khởi tạo app một instance duy nhất bằng `QLocalServer`.
- Tạo/cập nhật cấu hình tại `%USERPROFILE%\.cleanbox\config.json`.
- Ở lần chạy đầu, tự thêm `Downloads` và Recycle Bin vào danh sách dọn dẹp.
- Khởi chạy theo dõi dung lượng ổ đĩa định kỳ.

## Tính năng chính

- Chạy nền với khay hệ thống (tray): `Clean Now`, `Settings`, `Exit`.
- Dọn dẹp thư mục theo danh sách người dùng cấu hình, có hộp thoại xác nhận trước khi xóa.
- Chạy dọn dẹp nền qua `CleanupProgressWorker` và hiển thị tiến độ trên UI/tray.
- Theo dõi dung lượng ổ đĩa, cảnh báo low-space theo ngưỡng cấu hình.
- Cơ chế chống spam cảnh báo theo từng ổ (cooldown 24h) và reset khi ổ hồi phục dung lượng.
- Storage Analyzer:
  - Quét thư mục theo thời gian thực (`scan_children_realtime`).
  - Lazy expand khi mở node cây.
  - Bộ nhớ đệm điều hướng Back/Forward.
  - Context menu: thêm vào danh sách dọn dẹp, xóa vào Recycle Bin, mở vị trí file.
- Bảo vệ thư mục hệ thống ở nhiều lớp (`ConfigManager`, `CleanupService`, thao tác từ Storage View).
- Tự khởi động cùng Windows bằng Registry, có fallback Task Scheduler nếu cần.

## Công nghệ

- Python 3.11+
- PyQt6
- pystray + Pillow
- psutil
- winshell + pywin32
- win11toast
- PyInstaller + NSIS (release pipeline)

## Cấu trúc dự án

- `src/main.py`: entrypoint, thiết lập logging.
- `src/app.py`: orchestration vòng đời ứng dụng, signal wiring, startup/shutdown.
- `src/features/cleanup/`: dọn dẹp thư mục + worker nền.
- `src/features/folder_scanner/`: engine quét thư mục và tính toán kích thước.
- `src/features/storage_monitor/`: polling ổ đĩa, phát hiện low-space, cooldown.
- `src/features/notifications/`: gửi toast/tray notification.
- `src/shared/`: constants, config, auto-start registry, elevation, utils.
- `src/ui/`: MainWindow, tray icon, các view Storage/Cleanup/Settings.
- `tests/`: unit/component/integration/e2e/ui.
- `quality/`: script kiểm tra chất lượng trước release.
- `docs/`: tài liệu BA/TA/yêu cầu/API.

## Cấu hình runtime

File cấu hình: `%USERPROFILE%\.cleanbox\config.json`

Các khóa chính:
- `cleanup_directories`
- `first_run_complete`
- `low_space_threshold_gb`
- `polling_interval_seconds`
- `auto_start_enabled`
- `notified_drives`

Chi tiết hành vi:
- `ConfigManager` ghi file theo cơ chế atomic + backup (`.json.bak`).
- Tự lọc bỏ đường dẫn hệ thống được bảo vệ khỏi danh sách dọn dẹp.
- Lưu trạng thái ổ đĩa đã cảnh báo để duy trì cooldown qua lần mở app sau.

## Phát triển

```powershell
pytest
python -m flake8 src tests
python quality/verify_release.py
python build_local.py
```

Ghi chú:
- `build_local.py` build artifact local bằng Nuitka (tùy chọn NSIS).
- `.github/workflows/release.yml` dùng cho release theo tag `v*`.

## Tài liệu

- Kiến trúc: `ARCHITECTURE.md`
- API cục bộ: `docs/API.md`
- Yêu cầu: `docs/requirements.md`
- Business Analysis: `docs/business-analysis/README.md`
- Technical Analysis: `docs/technical-analysis/README.md`

## Giới hạn hiện tại

- Ứng dụng chỉ hỗ trợ Windows.
- Không có HTTP API public (chỉ desktop app local).
- Nhãn version ở footer Settings hiện còn hardcode `v1.0.0` trong UI, chưa đồng bộ với `VERSION` (`1.0.18`).

## License

MIT
