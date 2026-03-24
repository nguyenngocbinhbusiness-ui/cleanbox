# Lịch sử thay đổi

## [1.0.19] - 2026-03-23

### Changed
- Đồng bộ version metadata ở Settings View, build local, và tài liệu tham chiếu theo baseline hiện hành.
- Loại bỏ ghi chú version cứng cũ trong tài liệu vận hành và yêu cầu.
- Cập nhật release/build metadata về `1.0.19` để khớp `VERSION`.

### Fixed
- Footer Settings đọc version động từ `VERSION`, tránh lệch giữa UI, build và tài liệu.

## [1.0.18] - 2026-03-20

### Added
- Bổ sung thống kê độ đầy đủ của kết quả quét thư mục (`scanned_files`, `scanned_dirs`, bộ đếm skip và lý do skip).
- Thêm cơ chế session isolation cho realtime scan UI để bỏ qua signal cũ sau khi hủy/chạy lại.
- Thêm test hồi quy cho tổng hợp scan stats và xử lý stale-session signal.

### Changed
- Scanner chuyển sang stream `os.scandir()` thay vì materialize toàn bộ danh sách, giảm spike bộ nhớ với thư mục lớn.
- Số worker scanner chạy song song được điều chỉnh theo CPU và có thể cấu hình qua `CLEANBOX_SCANNER_WORKERS`.
- Text trạng thái hoàn tất realtime scan hiển thị thêm thống kê completeness khi có dữ liệu.

### Fixed
- Luồng cancel scan hiện invalidates session đang chạy và xóa buffer child update đang chờ.
- Ổn định unit test bằng cách loại bỏ side effect từ dialog modal và đồng bộ mock ở luồng entrypoint admin.

---

## [1.0.17] - 2026-01-09

### Fixed
- Sửa tương thích Python 3.11 cho f-string (tránh cú pháp chỉ có ở Python 3.12+).
- Chuyển multi-line f-string sang dạng single-line ở một số vị trí.
- File đã chỉnh: `notifications/service.py`, `storage_view.py`.

---

## [1.0.16] - 2026-01-09

### Changed
- Bản phát hành nội bộ phục vụ đồng bộ pipeline.

---

## [1.0.14] - 2026-01-09

### Changed
- Bản phát hành nội bộ phục vụ đồng bộ pipeline.

---

## [1.0.12] - 2026-01-09

### Changed
- Bản phát hành nội bộ phục vụ đồng bộ pipeline.

---

## [1.0.10] - 2026-01-08

### Changed
- Bản phát hành nội bộ phục vụ đồng bộ pipeline.

---

## [1.0.9] - 2026-01-08

### Fixed
- Sửa build để bundle assets đúng bằng `--add-data`.
- Icon và tài nguyên hoạt động đúng trong release build.

---

## [1.0.8] - 2026-01-08

### Fixed
- Sửa workflow release theo đúng phạm vi Windows-only.
- Cải thiện đóng gói artifact theo quy ước tên bản phát hành.

---

## [1.0.7] - 2026-01-08

### Changed
- Cải thiện GitHub Actions release workflow.
- Chuẩn hóa tên artifact theo prefix phiên bản.
- Thêm release notes tự động.

---

## [1.0.6] - 2026-01-08

### Added
- Thêm icon ứng dụng (`icon.ico`).
- Thêm test cho constants và registry.

### Changed
- Cải thiện logic trong `app.py` và cấu hình constants.

---

## [1.0.5] - 2026-01-06

### Changed
- Bản build mới với cải tiến icon.
- Đồng bộ các thay đổi đang chờ.

---

## [1.0.3] - 2026-01-06

### Changed
- Bản vá ổn định.

---

## [1.0.2] - 2026-01-06

### Changed
- Dọn dẹp workflow.
- Sửa thứ tự import ở entrypoint.
- Loại bỏ Dockerfile không dùng.

---

## [1.0.1] - 2026-01-05

### Changed
- Thêm GitHub Actions workflow cho release tự động.

---

## [1.0.0] - 2024-06-01

### Added
- Bản phát hành đầu tiên của CleanBox.
- Công cụ dọn dẹp ổ đĩa với khay hệ thống.
