# Risk Matrix Method

## 1. Tổng quan (Overview)

**Risk Matrix** (Ma trận rủi ro) là phương pháp đánh giá rủi ro bán định lượng, sử dụng ma trận hai chiều để phân loại và ưu tiên các rủi ro dựa trên hai yếu tố chính:

- **Likelihood (Khả năng xảy ra)**: Xác suất một sự kiện rủi ro xảy ra
- **Severity / Impact (Mức độ nghiêm trọng)**: Hậu quả khi rủi ro xảy ra

Phương pháp này được sử dụng rộng rãi trong ISO 31000, IEC 61508, ISO 14971 và nhiều tiêu chuẩn quản lý rủi ro khác.

## 2. Mục đích áp dụng

| Mục đích | Mô tả |
|----------|-------|
| Nhận diện rủi ro | Liệt kê và phân loại các rủi ro tiềm ẩn |
| Đánh giá rủi ro | Xếp hạng rủi ro theo mức độ ưu tiên |
| Ra quyết định | Hỗ trợ quyết định biện pháp xử lý phù hợp |
| Giao tiếp | Trực quan hóa rủi ro cho stakeholders |

## 3. Cấu trúc Risk Matrix

### 3.1 Thang đo Likelihood (Khả năng xảy ra)

| Level | Tên gọi | Mô tả | Tần suất tham khảo |
|-------|---------|-------|---------------------|
| 1 | Rare (Rất hiếm) | Hầu như không xảy ra | < 1 lần / 10 năm |
| 2 | Unlikely (Ít xảy ra) | Có thể xảy ra nhưng hiếm | 1 lần / 5-10 năm |
| 3 | Possible (Có thể) | Có thể xảy ra | 1 lần / 1-5 năm |
| 4 | Likely (Nhiều khả năng) | Có khả năng cao xảy ra | 1 lần / tháng-năm |
| 5 | Almost Certain (Gần như chắc chắn) | Xảy ra thường xuyên | > 1 lần / tháng |

### 3.2 Thang đo Severity (Mức độ nghiêm trọng)

| Level | Tên gọi | Mô tả |
|-------|---------|-------|
| 1 | Negligible (Không đáng kể) | Ảnh hưởng rất nhỏ, không cần xử lý |
| 2 | Minor (Nhẹ) | Ảnh hưởng nhỏ, có thể tự khắc phục |
| 3 | Moderate (Trung bình) | Ảnh hưởng đáng kể, cần có biện pháp |
| 4 | Major (Nghiêm trọng) | Ảnh hưởng lớn, cần xử lý ngay |
| 5 | Catastrophic (Thảm họa) | Ảnh hưởng cực kỳ nghiêm trọng |

### 3.3 Ma trận rủi ro 5×5

```
                        SEVERITY (Mức độ nghiêm trọng)
                   1          2          3          4          5
              Negligible   Minor    Moderate    Major   Catastrophic
         ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    5    │    5     │    10    │    15    │    20    │    25    │  Almost Certain
 L       ├──────────┼──────────┼──────────┼──────────┼──────────┤
 I  4    │    4     │     8    │    12    │    16    │    20    │  Likely
 K       ├──────────┼──────────┼──────────┼──────────┼──────────┤
 E  3    │    3     │     6    │     9    │    12    │    15    │  Possible
 L       ├──────────┼──────────┼──────────┼──────────┼──────────┤
 I  2    │    2     │     4    │     6    │     8    │    10    │  Unlikely
 H       ├──────────┼──────────┼──────────┼──────────┼──────────┤
 O  1    │    1     │     2    │     3    │     4    │     5    │  Rare
 O       └──────────┴──────────┴──────────┴──────────┴──────────┘
 D

  Risk Score = Likelihood × Severity
```

### 3.4 Phân loại mức rủi ro

| Risk Score | Mức rủi ro | Màu sắc | Hành động yêu cầu |
|------------|-----------|----------|-------------------|
| 1-3 | Low (Thấp) | 🟢 Xanh lá | Chấp nhận, theo dõi định kỳ |
| 4-6 | Medium (Trung bình) | 🟡 Vàng | Cần biện pháp giảm thiểu, theo dõi |
| 8-12 | High (Cao) | 🟠 Cam | Phải có biện pháp xử lý, ưu tiên cao |
| 15-25 | Critical (Rất cao) | 🔴 Đỏ | Hành động ngay lập tức, không chấp nhận |

## 4. Quy trình thực hiện

### Bước 1: Nhận diện rủi ro (Hazard Identification)
- Brainstorming với các stakeholders
- Phân tích lịch sử sự cố
- Review tài liệu thiết kế và yêu cầu
- Sử dụng checklist theo domain

### Bước 2: Phân tích rủi ro (Risk Analysis)
- Xác định khả năng xảy ra (Likelihood)
- Xác định mức độ nghiêm trọng (Severity)
- Tính Risk Score = Likelihood × Severity

### Bước 3: Đánh giá rủi ro (Risk Evaluation)
- Xếp hạng rủi ro theo Risk Score
- So sánh với ngưỡng chấp nhận (Risk Acceptance Criteria)
- Xác định rủi ro cần xử lý

### Bước 4: Xử lý rủi ro (Risk Treatment)
- **Avoid** (Tránh): Loại bỏ nguồn rủi ro
- **Mitigate** (Giảm thiểu): Giảm likelihood hoặc severity
- **Transfer** (Chuyển giao): Bảo hiểm, outsource
- **Accept** (Chấp nhận): Chấp nhận với giám sát

### Bước 5: Theo dõi và đánh giá lại (Monitoring & Review)
- Cập nhật Risk Matrix định kỳ
- Đánh giá lại sau khi áp dụng biện pháp
- Ghi nhận rủi ro mới phát sinh

## 5. Template áp dụng cho dự án phần mềm

| ID | Rủi ro | Mô tả | Likelihood (1-5) | Severity (1-5) | Risk Score | Mức rủi ro | Biện pháp xử lý | Owner | Trạng thái |
|----|--------|-------|-------------------|-----------------|------------|------------|-----------------|-------|------------|
| R-001 | [Tên rủi ro] | [Mô tả chi tiết] | [1-5] | [1-5] | [L×S] | [Low/Med/High/Critical] | [Biện pháp] | [Người chịu trách nhiệm] | [Open/Mitigated/Closed] |

## 6. Phân tích rủi ro dự án CleanBox (Project Risk Analysis)

### 6.1 Bối cảnh dự án

**CleanBox** là ứng dụng Windows desktop chạy nền, giám sát dung lượng ổ đĩa và cho phép dọn dẹp thư mục bằng một cú click. Các module chính: Cleanup Service, Storage Monitor, Notifications, Folder Scanner, System Tray, Config Manager, Auto-start Registry.

### 6.2 Risk Register — CleanBox

| ID | Rủi ro | Mô tả | Likelihood (1-5) | Severity (1-5) | Risk Score | Mức rủi ro | Biện pháp xử lý | Owner | Trạng thái |
|----|--------|-------|-------------------|-----------------|------------|------------|-----------------|-------|------------|
| R-001 | Xóa nhầm dữ liệu quan trọng | User thêm thư mục chứa dữ liệu quan trọng vào cleanup list, cleanup xóa hết | 3 | 5 | 15 | 🔴 Critical | Confirmation dialog trước khi xóa; whitelist system folders; preview trước cleanup | Dev Lead | Open |
| R-002 | Memory leak do StorageMonitor | QTimer polling mỗi 60s, psutil calls tích tụ memory qua thời gian | 3 | 3 | 9 | 🟠 High | Memory profiling; giới hạn object lifetime; unit test leak detection | Dev | Open |
| R-003 | Race condition giữa cleanup worker và UI | CleanupProgressWorker (QThread) truy cập shared state cùng lúc với main thread | 2 | 4 | 8 | 🟠 High | Signal/Slot pattern (đã có); review thread-safety cho ConfigManager | Dev | Mitigated |
| R-004 | Recycle Bin API failure (winshell) | winshell.recycle_bin() throw exception trên một số Windows version | 3 | 3 | 9 | 🟠 High | Try/catch wrapper; fallback mechanism; test trên Win10/11 variants | QA | Open |
| R-005 | Registry auto-start bị antivirus block | Antivirus/Group Policy chặn write registry HKCU\Run | 4 | 2 | 8 | 🟠 High | Graceful error handling; thông báo user; fallback Task Scheduler | Dev | Open |
| R-006 | Config file corruption | config.json bị corrupt do crash/power loss trong lúc write | 2 | 4 | 8 | 🟠 High | Atomic write (write temp → rename); backup config; validate on load | Dev | Open |
| R-007 | Notification spam | StorageMonitor gửi toast liên tục khi ổ đĩa luôn < threshold | 3 | 2 | 6 | 🟡 Medium | Cooldown mechanism; notified_drives tracking (đã có); per-drive cooldown timer | Dev | Mitigated |
| R-008 | Single instance lock failure | QLocalServer lock không release khi app crash → không mở lại được | 2 | 3 | 6 | 🟡 Medium | Stale lock detection; timeout mechanism; cleanup on crash | Dev | Open |
| R-009 | PyInstaller bundle thiếu dependency | Exe bundle thiếu DLL/resource → crash on specific machines | 2 | 3 | 6 | 🟡 Medium | CI/CD test trên clean VM; smoke test after build | QA | Open |
| R-010 | Folder scanner timeout trên ổ lớn | FolderScanner (ThreadPoolExecutor) scan ổ đĩa TB+ → UI freeze hoặc OOM | 3 | 2 | 6 | 🟡 Medium | Scan depth limit; cancellation support; progressive loading | Dev | Open |
| R-011 | UI không responsive khi cleanup | Nếu signal/slot bị block, UI freeze trong quá trình cleanup | 2 | 2 | 4 | 🟡 Medium | QThread đã tách biệt (đã có); verify signal emission timing | QA | Mitigated |
| R-012 | Thiếu logging cho troubleshooting | Lỗi xảy ra nhưng không đủ log để debug | 3 | 1 | 3 | 🟢 Low | Structured logging (đã có trong main.py); thêm log levels cho mỗi service | Dev | Mitigated |

### 6.3 Risk Matrix Visualization — CleanBox

```
                        SEVERITY (Mức độ nghiêm trọng)
                   1          2          3          4          5
              Negligible   Minor    Moderate    Major   Catastrophic
         ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    5    │          │          │          │          │          │
         ├──────────┼──────────┼──────────┼──────────┼──────────┤
    4    │          │  R-005   │          │          │          │
         ├──────────┼──────────┼──────────┼──────────┼──────────┤
    3    │  R-012   │ R-007    │ R-002    │          │  R-001   │
         │          │ R-010    │ R-004    │          │          │
         ├──────────┼──────────┼──────────┼──────────┼──────────┤
    2    │          │  R-011   │ R-008    │ R-003    │          │
         │          │          │ R-009    │ R-006    │          │
         ├──────────┼──────────┼──────────┼──────────┼──────────┤
    1    │          │          │          │          │          │
         └──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 6.4 Phân bổ rủi ro theo mức

| Mức rủi ro | Số lượng | IDs |
|------------|----------|-----|
| 🔴 Critical (15-25) | 1 | R-001 |
| 🟠 High (8-12) | 4 | R-002, R-003, R-004, R-005, R-006 |
| 🟡 Medium (4-6) | 5 | R-007, R-008, R-009, R-010, R-011 |
| 🟢 Low (1-3) | 1 | R-012 |

## 7. Kế hoạch triển khai và xác minh (Implementation & Verification Plan)

### 7.1 Ưu tiên xử lý

| Priority | Risk ID | Biện pháp | Verification Method |
|----------|---------|-----------|-------------------|
| P1 — Ngay lập tức | R-001 | Thêm confirmation dialog + folder whitelist + preview | Manual test: thêm system folder → bị block; E2E test cleanup flow |
| P2 — Sprint tiếp theo | R-006 | Atomic write cho ConfigManager | Unit test: simulate crash during write → config vẫn valid |
| P2 | R-002 | Memory profiling StorageMonitor | Integration test: chạy 1000 polling cycles, đo memory delta < 5MB |
| P2 | R-004 | Wrap winshell API với fallback | Unit test: mock winshell exception → fallback hoạt động |
| P3 — Backlog | R-005 | Graceful error + fallback scheduler | Manual test trên máy có Group Policy restricted |
| P3 | R-008 | Stale lock detection | Unit test: simulate stale lock file → app vẫn mở được |
| P3 | R-010 | Scan depth limit + cancellation | Integration test: scan directory 100K+ files → response < 30s |
| P4 — Monitor | R-003, R-007, R-011, R-012 | Đã mitigated, theo dõi | Code review + regression tests |

### 7.2 Verification Matrix

| Risk ID | Unit Test | Integration Test | E2E Test | Manual Test | Code Review |
|---------|-----------|-----------------|----------|-------------|-------------|
| R-001 | ✅ Whitelist logic | ✅ Cleanup + confirm | ✅ Full flow | ✅ System folders | ✅ |
| R-002 | — | ✅ Memory profiling | — | — | ✅ |
| R-003 | — | ✅ Concurrent access | — | — | ✅ |
| R-004 | ✅ Mock winshell | ✅ Recycle bin ops | — | ✅ Multi-OS | ✅ |
| R-005 | ✅ Mock registry | — | — | ✅ GP-restricted | ✅ |
| R-006 | ✅ Atomic write | ✅ Crash simulation | — | — | ✅ |
| R-007 | ✅ Cooldown timer | — | — | ✅ Low disk scenario | — |
| R-008 | ✅ Stale lock | ✅ Multi-instance | — | — | — |
| R-009 | — | — | ✅ Clean VM | ✅ Fresh install | — |
| R-010 | — | ✅ Large dir scan | — | ✅ TB drive | ✅ |

### 7.3 Tiêu chí chấp nhận (Acceptance Criteria)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Critical risks (15-25) | 0 open | All mitigated or eliminated |
| High risks (8-12) | Tất cả có action plan | Review mỗi sprint |
| Medium risks (4-6) | Có owner assigned | Monthly review |
| Risk re-assessment frequency | Mỗi release | Trước khi publish version mới |
| Test coverage cho mitigations | ≥ 90% | pytest-cov report |

## 8. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Đơn giản, dễ hiểu và dễ áp dụng
- ✅ Trực quan, phù hợp giao tiếp với stakeholders
- ✅ Linh hoạt, áp dụng cho nhiều loại dự án
- ✅ Không yêu cầu dữ liệu thống kê phức tạp

### Hạn chế
- ❌ Mang tính chủ quan (phụ thuộc đánh giá cá nhân)
- ❌ Khó phân biệt rủi ro có cùng Risk Score
- ❌ Không thể hiện mối quan hệ giữa các rủi ro
- ❌ Có thể dẫn đến "risk binning" (gom nhóm sai)

## 9. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| ISO 31000:2018 | Quản lý rủi ro - Nguyên tắc và hướng dẫn |
| ISO 31010:2019 | Kỹ thuật đánh giá rủi ro |
| IEC 61508 | An toàn chức năng hệ thống E/E/PE |
| ISO 14971:2019 | Quản lý rủi ro thiết bị y tế |
| MIL-STD-882E | Hệ thống an toàn quốc phòng |

## 10. Tài liệu tham khảo

1. ISO 31000:2018 - Risk management — Guidelines
2. ISO 31010:2019 - Risk assessment techniques
3. Cox, L.A. (2008) - "What's Wrong with Risk Matrices?" Risk Analysis, 28(2)
4. Duijm, N.J. (2015) - "Recommendations on the use and design of risk matrices"
5. NIST SP 800-30 - Guide for Conducting Risk Assessments
