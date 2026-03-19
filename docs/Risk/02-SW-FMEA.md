# SW-FMEA (Software Failure Mode and Effects Analysis)

## 1. Tổng quan (Overview)

**SW-FMEA** (Software Failure Mode and Effects Analysis) là phương pháp phân tích rủi ro có hệ thống, tập trung vào việc nhận diện các **failure mode** (chế độ hỏng hóc) tiềm ẩn trong phần mềm, phân tích **nguyên nhân** và **hậu quả** của từng failure mode, từ đó đề xuất biện pháp phòng ngừa và giảm thiểu rủi ro.

SW-FMEA là biến thể của FMEA truyền thống (IEC 60812), được điều chỉnh cho đặc thù phần mềm — nơi lỗi không đến từ mài mòn vật lý mà từ lỗi thiết kế, logic, dữ liệu, và tương tác hệ thống.

## 2. Khái niệm cốt lõi

### 2.1 Failure Mode (Chế độ hỏng hóc)
Cách thức mà một thành phần phần mềm có thể thất bại trong việc thực hiện chức năng yêu cầu.

**Các loại failure mode phần mềm phổ biến:**

| Loại | Mô tả | Ví dụ |
|------|--------|-------|
| Function failure | Chức năng không thực hiện được | API không trả về response |
| Incorrect output | Đầu ra sai | Tính toán sai giá trị |
| Timing failure | Không đáp ứng yêu cầu thời gian | Timeout quá lâu |
| Data corruption | Dữ liệu bị hỏng / mất | Database corruption |
| Interface failure | Lỗi giao tiếp giữa các module | Message format mismatch |
| Resource exhaustion | Cạn kiệt tài nguyên | Memory leak, disk full |
| Security failure | Vi phạm bảo mật | Unauthorized access |

### 2.2 RPN (Risk Priority Number)

```
RPN = Severity (S) × Occurrence (O) × Detection (D)
```

- **Severity (S)**: Mức độ nghiêm trọng của hậu quả (1-10)
- **Occurrence (O)**: Khả năng xảy ra của failure mode (1-10)
- **Detection (D)**: Khả năng phát hiện trước khi ảnh hưởng đến người dùng (1-10)

> **Lưu ý**: Detection score **ngược** — điểm cao = khó phát hiện = rủi ro cao hơn

## 3. Thang đo chi tiết

### 3.1 Severity (Mức độ nghiêm trọng)

| Score | Mức độ | Mô tả (Software context) |
|-------|--------|--------------------------|
| 1 | None | Không ảnh hưởng, người dùng không nhận ra |
| 2-3 | Low | Ảnh hưởng nhẹ, có workaround dễ dàng |
| 4-5 | Moderate | Chức năng bị giảm, cần restart/reload |
| 6-7 | High | Mất chức năng quan trọng, data loss cục bộ |
| 8-9 | Very High | System crash, data loss nghiêm trọng, bảo mật bị xâm phạm |
| 10 | Hazardous | Ảnh hưởng an toàn con người, thiệt hại không thể khắc phục |

### 3.2 Occurrence (Khả năng xảy ra)

| Score | Mức độ | Tần suất tham khảo |
|-------|--------|---------------------|
| 1 | Almost impossible | < 1 / 1,000,000 operations |
| 2-3 | Remote | 1 / 100,000 operations |
| 4-5 | Occasional | 1 / 10,000 operations |
| 6-7 | Frequent | 1 / 1,000 operations |
| 8-9 | High | 1 / 100 operations |
| 10 | Very High | > 1 / 10 operations |

### 3.3 Detection (Khả năng phát hiện)

| Score | Mức độ | Mô tả |
|-------|--------|-------|
| 1 | Almost certain | Automated test, CI/CD pipeline tự động phát hiện |
| 2-3 | High | Code review, static analysis tool phát hiện được |
| 4-5 | Moderate | Phát hiện qua integration/system testing |
| 6-7 | Low | Chỉ phát hiện qua UAT hoặc beta testing |
| 8-9 | Very low | Chỉ phát hiện khi xảy ra trong production |
| 10 | Impossible | Không có cơ chế phát hiện |

## 4. Quy trình thực hiện SW-FMEA

### Phase 1: Preparation (Chuẩn bị)
1. Xác định phạm vi phân tích (scope)
2. Thu thập tài liệu: requirements, architecture, design docs
3. Thành lập team FMEA (dev, QA, architect, domain expert)
4. Xác định function/component cần phân tích

### Phase 2: Analysis (Phân tích)
1. **Liệt kê chức năng**: Mỗi module/component làm gì?
2. **Nhận diện Failure Modes**: Mỗi chức năng có thể fail như thế nào?
3. **Xác định Effects**: Hậu quả của từng failure mode?
4. **Xác định Causes**: Nguyên nhân gốc rễ?
5. **Đánh giá S, O, D**: Cho điểm từng yếu tố
6. **Tính RPN**: S × O × D

### Phase 3: Action (Hành động)
1. Xếp hạng ưu tiên theo RPN
2. Đề xuất **Recommended Actions**
3. Gán owner và deadline
4. Thực hiện corrective/preventive actions

### Phase 4: Re-evaluation (Đánh giá lại)
1. Đánh giá lại S, O, D sau khi thực hiện action
2. Tính RPN mới
3. Xác nhận RPN giảm xuống mức chấp nhận được

## 5. SW-FMEA Worksheet Template

| ID | Component / Function | Failure Mode | Effect of Failure | S | Cause of Failure | O | Current Controls | D | RPN | Recommended Action | Owner | Target Date | Action Taken | New S | New O | New D | New RPN |
|----|---------------------|-------------|-------------------|---|------------------|---|-----------------|---|-----|-------------------|-------|-------------|-------------|-------|-------|-------|---------|
| FM-001 | [Module/Function] | [Cách thức fail] | [Hậu quả] | [1-10] | [Nguyên nhân] | [1-10] | [Biện pháp hiện tại] | [1-10] | [S×O×D] | [Đề xuất] | [Owner] | [Date] | [Đã thực hiện] | [1-10] | [1-10] | [1-10] | [S×O×D] |

## 6. Ví dụ áp dụng cho phần mềm

### Ví dụ: Module Authentication

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|
| FM-001 | User Login | Cho phép đăng nhập không hợp lệ | Unauthorized access, data breach | 9 | SQL injection trong login query | 3 | Input validation, parameterized query | 2 | 54 |
| FM-002 | Session Management | Session không expire | Hijacking session | 8 | Missing session timeout config | 4 | Session timeout = 30min | 3 | 96 |
| FM-003 | Password Reset | Gửi reset link cho email sai | Unauthorized password change | 8 | Email validation không chặt | 3 | Email verification step | 4 | 96 |
| FM-004 | Token Validation | Accept expired token | Replay attack | 7 | JWT expiry check bypass | 2 | Token expiry validation in middleware | 2 | 28 |

## 7. Phân tích SW-FMEA dự án CleanBox (Project Analysis)

### 7.1 Phạm vi phân tích

**Hệ thống**: CleanBox Desktop Application v1.0.17
**Modules phân tích**: Cleanup Service, Storage Monitor, Config Manager, Notifications, System Tray, Folder Scanner

### 7.2 SW-FMEA Worksheet — CleanBox

#### Module: Cleanup Service (`features/cleanup/service.py`)

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN | Recommended Action |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|-------------------|
| FM-CB-001 | cleanup_directory() | Xóa nhầm file quan trọng | Mất dữ liệu không phục hồi | 10 | User thêm thư mục hệ thống vào list | 3 | Không có whitelist | 8 | 240 | Thêm system folder whitelist + confirmation dialog |
| FM-CB-002 | cleanup_directory() | Không xóa được file (PermissionError) | Cleanup incomplete, user thấy lỗi | 4 | File đang bị lock bởi process khác | 5 | @retry decorator | 3 | 60 | Skip locked files + log + report |
| FM-CB-003 | empty_recycle_bin() | winshell API crash | Cleanup fail, exception propagate | 6 | winshell incompatible với Windows version | 3 | Try/catch cơ bản | 4 | 72 | Wrap với fallback mechanism + OS version check |
| FM-CB-004 | CleanupProgressWorker | Worker thread crash | UI nhận signal cleanup_finished với error | 5 | Unhandled exception trong QThread | 2 | Basic exception handling | 5 | 50 | Global exception handler trong worker + error signal |

#### Module: Storage Monitor (`features/storage_monitor/service.py`)

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN | Recommended Action |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|-------------------|
| FM-CB-005 | QTimer polling | Memory leak tích tụ | App chiếm ngày càng nhiều RAM | 5 | psutil objects không được release | 3 | Không có monitoring | 7 | 105 | Memory profiling + object cleanup mỗi cycle |
| FM-CB-006 | low_space_detected signal | Notification spam | User tắt app do bị làm phiền | 3 | Ổ đĩa luôn dưới threshold | 4 | notified_drives set | 3 | 36 | Per-drive cooldown timer (24h) |
| FM-CB-007 | get_all_drives() | Crash khi USB disconnect | App crash nếu drive bị remove during scan | 6 | psutil.disk_partitions() trả về stale info | 2 | Không có handling | 6 | 72 | Try/catch per drive + skip unavailable |

#### Module: Config Manager (`shared/config/manager.py`)

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN | Recommended Action |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|-------------------|
| FM-CB-008 | save config (JSON write) | Config file corrupt | Mất toàn bộ config, app reset default | 7 | Power loss / crash during file write | 2 | Không có atomic write | 8 | 112 | Atomic write (temp file → rename) + backup |
| FM-CB-009 | load config | Crash khi JSON invalid | App không start được | 7 | Manual edit sai format | 2 | Basic JSON parse | 5 | 70 | JSON schema validation + fallback to defaults |
| FM-CB-010 | cleanup_directories list | Chứa path không tồn tại | Cleanup báo error cho non-existent paths | 3 | User xóa folder sau khi config | 4 | Không có validation | 4 | 48 | Validate paths trước cleanup + remove invalid |

#### Module: System Tray & UI

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN | Recommended Action |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|-------------------|
| FM-CB-011 | TrayIcon (pystray) | Tray icon biến mất | User không thể tương tác | 5 | pystray thread crash | 2 | Separate thread | 7 | 70 | Health check + auto-restart tray thread |
| FM-CB-012 | QLocalServer lock | Không mở app lần 2 | User phải force kill process | 4 | Stale lock từ previous crash | 2 | Lock file detection | 5 | 40 | Timeout + stale lock cleanup |
| FM-CB-013 | Registry auto-start | Auto-start bị block | App không chạy khi boot | 3 | Antivirus / Group Policy | 4 | Không có fallback | 6 | 72 | Error notification + Task Scheduler fallback |

#### Module: Folder Scanner (`features/folder_scanner/service.py`)

| ID | Function | Failure Mode | Effect | S | Cause | O | Current Controls | D | RPN | Recommended Action |
|----|----------|-------------|--------|---|-------|---|-----------------|---|-----|-------------------|
| FM-CB-014 | ThreadPoolExecutor scan | OOM khi scan ổ lớn | App crash | 6 | Đệ quy sâu trên ổ TB+ | 3 | Không có limit | 5 | 90 | Max depth limit + lazy loading + cancellation |
| FM-CB-015 | Progress callback | UI freeze | User nghĩ app treo | 4 | Callback quá frequent block main thread | 3 | Separate thread | 3 | 36 | Throttle callback frequency (max 10/s) |

### 7.3 RPN Ranking — Top Critical Items

| Rank | ID | Failure Mode | RPN | Priority |
|------|-----|-------------|-----|----------|
| 1 | FM-CB-001 | Xóa nhầm file quan trọng | 240 | 🔴 CRITICAL — Block release |
| 2 | FM-CB-008 | Config file corrupt | 112 | 🔴 HIGH — Must fix |
| 3 | FM-CB-005 | Memory leak StorageMonitor | 105 | 🟠 HIGH — Must fix |
| 4 | FM-CB-014 | OOM khi scan ổ lớn | 90 | 🟠 HIGH — Must fix |
| 5 | FM-CB-003 | winshell API crash | 72 | 🟠 MEDIUM — Plan fix |
| 6 | FM-CB-007 | Crash khi USB disconnect | 72 | 🟠 MEDIUM — Plan fix |
| 7 | FM-CB-013 | Auto-start bị block | 72 | 🟠 MEDIUM — Plan fix |

## 8. Kế hoạch triển khai và xác minh (Implementation & Verification Plan)

### 8.1 Action Plan theo RPN Priority

| ID | RPN | Action | Implementation | Verification | Owner | Target |
|----|-----|--------|---------------|-------------|-------|--------|
| FM-CB-001 | 240 | System folder whitelist + confirm dialog | Thêm PROTECTED_PATHS constant + QMessageBox confirm | Unit test: whitelist blocks system paths; E2E: confirm dialog appears | Dev Lead | v1.1.0 |
| FM-CB-008 | 112 | Atomic write cho config | Write to .tmp → os.rename → delete .tmp | Unit test: interrupt write → config intact; Integration: crash simulation | Dev | v1.1.0 |
| FM-CB-005 | 105 | Memory cleanup trong polling loop | Explicit del psutil objects + gc.collect() mỗi N cycles | Integration test: 10000 cycles, memory delta < 10MB | Dev | v1.1.0 |
| FM-CB-014 | 90 | Scan depth limit + cancel | Thêm max_depth param + threading.Event cho cancel | Unit test: scan stops at max_depth; Integration: cancel during scan | Dev | v1.1.0 |
| FM-CB-003 | 72 | winshell fallback | Try winshell → catch → fallback SHEmptyRecycleBin via ctypes | Unit test: mock winshell fail → fallback works | Dev | v1.2.0 |
| FM-CB-007 | 72 | Drive disconnect handling | Try/except per drive in get_all_drives() | Unit test: mock stale partition → skip gracefully | Dev | v1.2.0 |
| FM-CB-013 | 72 | Registry fallback | Catch PermissionError → notify user + offer Task Scheduler | Manual test: restricted registry → fallback offered | Dev | v1.2.0 |

### 8.2 Verification Strategy

| Test Level | Scope | Tools | Target Coverage |
|-----------|-------|-------|----------------|
| Unit Tests | Từng function/method | pytest, pytest-mock | ≥ 90% cho critical modules |
| Integration Tests | Module interactions | pytest, pytest-qt | Signal/slot flows, file I/O |
| E2E Tests | Full user workflows | pytest-qt, QTest | Cleanup flow, settings flow |
| Regression Tests | Prevent re-introduction | CI/CD (GitHub Actions) | Run on every PR |
| Memory Tests | Leak detection | tracemalloc, memory_profiler | StorageMonitor, FolderScanner |

### 8.3 Re-evaluation Schedule

| Milestone | Action | Expected RPN Reduction |
|-----------|--------|----------------------|
| After v1.1.0 | Re-score FM-CB-001, 005, 008, 014 | RPN < 50 for all |
| After v1.2.0 | Re-score FM-CB-003, 007, 013 | RPN < 50 for all |
| Each release | Full FMEA review | No item > 100 RPN |

## 9. RPN Thresholds và Action Required

| RPN Range | Mức rủi ro | Hành động |
|-----------|-----------|-----------|
| 1-50 | Low | Acceptable, monitor |
| 51-100 | Medium | Cần action plan, cải thiện Detection |
| 101-200 | High | Phải có corrective action, ưu tiên cao |
| 201-1000 | Critical | Hành động ngay, không release khi chưa giải quyết |

## 10. Kỹ thuật hỗ trợ SW-FMEA

### 8.1 Nhận diện Failure Mode
- **5-Why Analysis**: Đào sâu nguyên nhân gốc rễ
- **Ishikawa Diagram**: Phân loại nguyên nhân
- **Code Review Findings**: Từ static/dynamic analysis
- **Bug History**: Phân tích pattern từ bug reports

### 8.2 Giảm Occurrence
- Design patterns (defensive programming)
- Input validation
- Error handling robustness
- Redundancy mechanisms

### 8.3 Tăng Detection (Giảm D score)
- Unit tests, integration tests
- Static analysis tools (SonarQube, ESLint)
- Runtime monitoring và alerting
- Chaos engineering / fault injection

## 11. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Phân tích có hệ thống, toàn diện
- ✅ Tập trung vào prevention (phòng ngừa)
- ✅ RPN cho phép ưu tiên hóa rõ ràng
- ✅ Tạo knowledge base về failure modes
- ✅ Phù hợp với quy trình phát triển phần mềm

### Hạn chế
- ❌ Tốn thời gian cho hệ thống lớn
- ❌ RPN có thể gây misleading (VD: S=9,O=1,D=1 = 9 vs S=3,O=3,D=3 = 27)
- ❌ Không phân tích được failure mode kết hợp (combined failures)
- ❌ Phụ thuộc vào kinh nghiệm của team

## 12. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| IEC 60812:2018 | FMEA/FMECA techniques |
| AIAG-VDA FMEA Handbook (2019) | FMEA handbook cho automotive |
| SAE J1739 | FMEA for design and process |
| ISO 26262 | Functional safety (automotive software) |
| DO-178C | Software for airborne systems |
| IEC 62304 | Medical device software lifecycle |

## 13. Tài liệu tham khảo

1. IEC 60812:2018 - Failure modes and effects analysis (FMEA and FMECA)
2. AIAG & VDA FMEA Handbook, 1st Edition, 2019
3. Stamatis, D.H. (2003) - "Failure Mode and Effect Analysis: FMEA from Theory to Execution"
4. Lutz, R.R. (1993) - "Analyzing Software Requirements Errors in Safety-Critical Embedded Systems"
5. NASA Technical Handbook - Software FMEA (NASA-HDBK-8739.18)
