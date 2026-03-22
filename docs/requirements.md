# Yêu cầu dự án CleanBox (Hiện hành)

## 1. Tổng quan

CleanBox là ứng dụng desktop chạy nền trên Windows để:
- Theo dõi dung lượng ổ đĩa.
- Cảnh báo khi dung lượng xuống thấp.
- Dọn dẹp nhanh các thư mục được cấu hình.
- Phân tích cấu trúc dung lượng thư mục theo dạng cây.

Tài liệu này phản ánh trạng thái phần mềm hiện tại (version `1.0.18`).

## 2. Phạm vi

### Trong phạm vi
- Chạy tray app (single instance).
- Auto-start cùng Windows.
- Theo dõi dung lượng nhiều ổ.
- Cảnh báo low-space có cooldown theo ổ.
- Cleanup đa thư mục + Recycle Bin marker.
- Storage Analyzer (scan realtime, lazy expand, context actions, cache điều hướng).
- Cấu hình threshold/interval/auto-start và lưu bền vững.
- Bảo vệ đường dẫn hệ thống khỏi thao tác xóa nguy hiểm.

### Ngoài phạm vi
- Lập lịch cleanup tự động.
- Cloud sync.
- Khôi phục dữ liệu đã xóa.
- API server từ xa.

## 3. User stories (đồng bộ với mã nguồn)

### Tray & vòng đời
- `US-001`: Người dùng muốn app tự khởi chạy cùng Windows.
  - Tiêu chí nghiệm thu:
    - [x] Có lưu và áp dụng `auto_start_enabled`.
    - [x] Hỗ trợ bật/tắt auto-start qua UI Settings.

- `US-002`: Người dùng muốn app chạy nền trong tray, không chiếm taskbar thường trực.
  - Tiêu chí nghiệm thu:
    - [x] Có tray icon và menu thao tác.
    - [x] Đóng cửa sổ chính chỉ ẩn (`hide`) thay vì thoát app.

### Monitoring
- `US-003`: Người dùng muốn nhận cảnh báo khi ổ đĩa gần đầy.
  - Tiêu chí nghiệm thu:
    - [x] Cảnh báo theo ngưỡng `low_space_threshold_gb`.
    - [x] Không spam cảnh báo liên tục (cooldown theo drive).
    - [x] Xóa trạng thái cảnh báo khi ổ phục hồi dung lượng.

### Cleanup
- `US-004`: Người dùng muốn cấu hình danh sách thư mục cần dọn.
  - Tiêu chí nghiệm thu:
    - [x] Thêm/xóa thư mục từ Cleanup View.
    - [x] Lưu bền vững trong config.
    - [x] Chặn thêm thư mục hệ thống protected.

- `US-005`: Người dùng muốn dọn dẹp nhanh một lần.
  - Tiêu chí nghiệm thu:
    - [x] Có xác nhận trước khi chạy cleanup.
    - [x] Cleanup chạy nền với progress bar.
    - [x] Có notification tổng kết kết quả.

### Storage Analyzer
- `US-006`: Người dùng muốn phân tích dung lượng thư mục theo cây.
  - Tiêu chí nghiệm thu:
    - [x] Có quét realtime theo node con.
    - [x] Có lazy expand khi mở node.
    - [x] Có Back/Forward dựa trên cache scan.

- `US-007`: Người dùng muốn thao tác nhanh trên thư mục trong kết quả quét.
  - Tiêu chí nghiệm thu:
    - [x] Có `Add to Cleanup`.
    - [x] Có `Delete` (move to Recycle Bin).
    - [x] Có `Open file location`.

### First-run
- `US-008`: Người dùng muốn app có cấu hình mặc định hợp lý ngay lần đầu.
  - Tiêu chí nghiệm thu:
    - [x] Tự thêm `Downloads` + Recycle Bin marker khi first run.

## 4. Yêu cầu chức năng

- `FR-001`: Đảm bảo single instance và có cơ chế gửi lệnh `show` từ instance thứ 2.
- `FR-002`: Cập nhật threshold và polling interval runtime khi đổi trong Settings.
- `FR-003`: Persist notified drive timestamps để duy trì cooldown qua các lần mở app.
- `FR-004`: Cấu hình phải ghi an toàn (atomic write + backup).
- `FR-005`: Các đường dẫn hệ thống protected phải bị chặn ở mọi luồng thêm/xóa/cleanup.

## 5. Yêu cầu phi chức năng

- `NFR-001`: Giao diện không bị treo khi cleanup hoặc scan lớn (dùng worker thread).
- `NFR-002`: Khả năng quan sát trạng thái tác vụ qua progress/status text/notification.
- `NFR-003`: Ứng dụng chỉ hỗ trợ Windows 10/11.
- `NFR-004`: Chịu lỗi cấu hình (fallback default, backup recovery).

## 6. Hạn chế đã biết

- Footer ở `SettingsView` đang hiển thị cứng `CleanBox v1.0.0`, chưa đồng bộ động theo version hiện hành.

## 7. Lịch sử cập nhật tài liệu

| Ngày | Thay đổi | Ghi chú |
|------|----------|--------|
| 2026-03-22 | Viết lại tài liệu yêu cầu theo trạng thái hiện tại | Đồng bộ với source code `1.0.18` |
