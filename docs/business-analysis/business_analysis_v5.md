---
document_type: business_analysis
version: 5
version_date: 2026-03-22
author: Codex Assistant
status: active
supersedes: ./business_analysis_v4.md
superseded_by: null
---

# Business Analysis v5 - CleanBox

## 1. Bối cảnh

Người dùng Windows thường thiếu công cụ nhẹ, chạy nền để:
- Theo dõi dung lượng ổ đĩa liên tục.
- Nhận cảnh báo sớm khi dung lượng sắp cạn.
- Dọn nhanh các thư mục rác thường gặp.
- Nhìn thấy bức tranh phân bổ dung lượng theo thư mục để quyết định dọn đúng chỗ.

## 2. Vấn đề kinh doanh

- Dung lượng cạn gây gián đoạn công việc.
- Dọn thủ công tốn thời gian và dễ bỏ sót.
- Nếu chỉ cảnh báo mà không có gợi ý/điểm thao tác ngay thì tỉ lệ xử lý thấp.

## 3. Mục tiêu

| ID | Mục tiêu | Chỉ số thành công |
|----|----------|-------------------|
| OBJ-001 | Cảnh báo sớm low-space | Người dùng nhận cảnh báo đúng ngưỡng cấu hình |
| OBJ-002 | Rút ngắn thao tác dọn dẹp | Có thể chạy cleanup từ tray hoặc view chính |
| OBJ-003 | Tăng khả năng ra quyết định | Storage Analyzer hiển thị cây thư mục và tỉ lệ dung lượng |
| OBJ-004 | Vận hành an toàn | Chặn thao tác cleanup/xóa trên thư mục hệ thống protected |

## 4. Phạm vi sản phẩm

### In-scope
- Tray app + single instance.
- Auto-start.
- Low-space monitor (threshold/interval cấu hình được).
- Cleanup workflow có xác nhận và progress.
- Storage Analyzer + context actions.
- Config persistence an toàn.

### Out-of-scope
- Cloud backup/recovery.
- Lập lịch cleanup theo cron/calendar.
- Tối ưu/tinh chỉnh nâng cao theo loại file chuyên sâu.

## 5. Persona chính

- Người dùng cá nhân hoặc văn phòng dùng Windows 10/11, cần công cụ nhẹ và thao tác nhanh.

## 6. Nhu cầu cốt lõi

- Biết ổ nào sắp đầy.
- Dọn được ngay với ít click.
- Tránh xóa nhầm vùng hệ thống quan trọng.
- Có góc nhìn tree-size để chọn thư mục cần dọn hiệu quả.

## 7. Use case trọng tâm

| Use case | Giá trị |
|----------|---------|
| Cảnh báo low-space | Phòng ngừa sự cố hết dung lượng |
| Clean Now từ tray | Giảm ma sát thao tác |
| Quét thư mục realtime | Xác định "thủ phạm" tốn dung lượng |
| Add to Cleanup từ cây thư mục | Chuyển từ phân tích sang hành động ngay |

## 8. Ràng buộc

- Chỉ Windows.
- Tích hợp sâu với khay hệ thống/registry/recycle bin nên phụ thuộc API hệ điều hành.

## 9. Rủi ro nghiệp vụ

- Hiển thị version trong UI chưa đồng bộ metadata có thể gây nhầm lẫn khi hỗ trợ người dùng.
- Nếu người dùng kỳ vọng tính năng scheduler cleanup, hiện tại chưa có trong phạm vi.

## 10. Khuyến nghị ưu tiên tiếp theo

1. Đồng bộ version hiển thị ở Settings với `VERSION`/`pyproject.toml`.
2. Bổ sung tài liệu sử dụng nhanh trong UI cho Storage Analyzer (help tooltip hoặc onboarding ngắn).
3. Cân nhắc roadmap cho cleanup theo lịch (ngoài phạm vi hiện tại).
