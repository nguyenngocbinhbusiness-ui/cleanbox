# HAZOP (Hazard and Operability Study)

## 1. Tổng quan (Overview)

**HAZOP** (Hazard and Operability Study — Nghiên cứu nguy hại và khả năng vận hành) là phương pháp phân tích rủi ro **có cấu trúc, teamwork-based**, sử dụng hệ thống **Guide Words** (từ khóa hướng dẫn) kết hợp với các **Process Parameters** (thông số quy trình) để nhận diện:

- **Hazards** (nguy hại): Các tình huống nguy hiểm
- **Operability problems** (vấn đề vận hành): Các sai lệch ảnh hưởng đến hiệu suất

HAZOP ban đầu được phát triển cho ngành công nghiệp hóa chất (ICI, 1960s), nhưng đã được điều chỉnh rộng rãi cho phần mềm, hệ thống IT, và các quy trình phức tạp.

## 2. Khái niệm cốt lõi

### 2.1 Design Intent
- Mục đích thiết kế / hành vi mong muốn của hệ thống
- Ví dụ: "API nhận request, validate, xử lý và trả response trong 200ms"

### 2.2 Guide Words
Từ khóa hướng dẫn giúp xác định các **deviations** (sai lệch) khỏi design intent.

| Guide Word | Ý nghĩa | Áp dụng phần mềm |
|-----------|---------|-------------------|
| **NO / NOT** | Không xảy ra | Chức năng không thực hiện |
| **MORE** | Nhiều hơn mong đợi | Response time dài hơn, data nhiều hơn |
| **LESS** | Ít hơn mong đợi | Throughput thấp hơn, data thiếu |
| **AS WELL AS** | Xảy ra thêm điều khác | Side effects không mong muốn |
| **PART OF** | Chỉ thực hiện một phần | Incomplete processing |
| **REVERSE** | Ngược lại | Data flow ngược, rollback thất bại |
| **OTHER THAN** | Khác hoàn toàn | Sai chức năng, wrong output type |
| **EARLY** | Quá sớm | Premature trigger, race condition |
| **LATE** | Quá muộn | Timeout, delayed response |
| **BEFORE** | Trước thứ tự | Out-of-order processing |
| **AFTER** | Sau thứ tự | Delayed action |

### 2.3 Process Parameters (Cho phần mềm)

| Parameter | Mô tả | Ví dụ |
|-----------|-------|-------|
| Flow | Luồng dữ liệu / xử lý | Data flow, request flow |
| Quantity | Số lượng | Record count, payload size |
| Quality | Chất lượng | Data accuracy, format validity |
| Timing | Thời gian | Response time, scheduling |
| Sequence | Thứ tự | Processing order, workflow steps |
| Composition | Thành phần | Data structure, message format |
| State | Trạng thái | System state, session state |
| Security | Bảo mật | Authentication, authorization |

### 2.4 Deviation = Guide Word + Parameter

| Guide Word | Parameter | Deviation | Ví dụ |
|-----------|-----------|-----------|-------|
| NO | Flow | Không có data flow | API không nhận được request |
| MORE | Quantity | Quá nhiều data | Payload quá lớn gây OOM |
| LESS | Quality | Chất lượng thấp | Data bị corrupt/invalid |
| REVERSE | Flow | Luồng ngược | Response gửi sai endpoint |
| LATE | Timing | Quá muộn | Timeout, stale data |
| OTHER THAN | Composition | Sai cấu trúc | Wrong message format |
| AS WELL AS | Security | Thêm quyền truy cập | Privilege escalation |
| PART OF | Sequence | Thiếu bước | Bỏ qua validation step |

## 3. Quy trình thực hiện HAZOP

### Phase 1: Planning & Preparation

#### Team composition (5-7 người)
| Vai trò | Trách nhiệm |
|---------|-------------|
| **Study Leader** | Điều phối, áp dụng guide words |
| **Scribe/Recorder** | Ghi nhận kết quả |
| **System Architect** | Giải thích design intent |
| **Developer** | Chi tiết implementation |
| **QA Engineer** | Testing perspective |
| **Domain Expert** | Business logic knowledge |
| **Operations** | Runtime/deployment knowledge |

#### Chuẩn bị tài liệu
- System architecture diagrams
- Data flow diagrams
- API specifications
- Requirements documents
- Previous incident reports

### Phase 2: Examination Sessions

1. **Chọn Node** (phần hệ thống cần phân tích)
2. **Xác định Design Intent** cho node
3. **Áp dụng Guide Words** cho từng parameter
4. **Với mỗi Deviation**:
   - Xác định **Causes** (nguyên nhân)
   - Xác định **Consequences** (hậu quả)
   - Xác định **Existing Safeguards** (biện pháp hiện có)
   - Đánh giá **Risk Level**
   - Đề xuất **Recommendations** (nếu cần)

### Phase 3: Documentation & Follow-up

1. Hoàn thiện HAZOP Worksheet
2. Assign actions và owners
3. Track implementation
4. Re-study nếu có thay đổi lớn

## 4. HAZOP Worksheet Template

| Node | Design Intent | Guide Word | Parameter | Deviation | Causes | Consequences | Existing Safeguards | Severity | Likelihood | Risk | Recommendations | Action By | Status |
|------|--------------|-----------|-----------|-----------|--------|-------------|-------------------|----------|------------|------|----------------|-----------|--------|
| [Module] | [Mục đích] | [GW] | [Param] | [GW + Param] | [Nguyên nhân] | [Hậu quả] | [Biện pháp hiện có] | [1-5] | [1-5] | [S×L] | [Đề xuất] | [Owner] | [Status] |

## 5. Ví dụ: HAZOP cho REST API Module

### Node: User Registration API

**Design Intent**: API nhận POST request với user data (name, email, password), validate, tạo user trong database, gửi confirmation email, và trả về HTTP 201 với user ID.

| Guide Word | Parameter | Deviation | Causes | Consequences | Safeguards | Risk | Recommendations |
|-----------|-----------|-----------|--------|-------------|------------|------|----------------|
| NO | Flow | Không nhận request | Server down, network issue, DNS failure | User không thể đăng ký | Health check, load balancer | Medium | Add circuit breaker, retry mechanism |
| MORE | Quantity | Quá nhiều request | DDoS, bot registration | Server overload, DoS | Rate limiting (100 req/min) | High | Implement CAPTCHA, improve rate limiting |
| LESS | Quality | Data không hợp lệ | Invalid email, weak password | Invalid user records | Input validation | Medium | Add comprehensive validation rules |
| OTHER THAN | Composition | Sai format request | Client bug, API version mismatch | 400 Error, confusion | JSON schema validation | Low | Add API versioning, clear error messages |
| AS WELL AS | Security | Inject malicious data | SQL injection, XSS | Data breach, compromised DB | Parameterized queries | High | Add WAF, CSP headers, escape output |
| PART OF | Sequence | Bỏ qua email confirmation | Email service down | Unverified accounts | Retry queue for emails | Medium | Implement async email with dead letter queue |
| LATE | Timing | Response quá chậm | DB slow, email service lag | Timeout, poor UX | Async email sending | Medium | Set DB query timeout, use message queue |
| REVERSE | Flow | Response gửi cho user sai | Session mixup, caching error | Privacy violation | Session management | High | Review session handling, disable response caching |
| EARLY | Timing | Request trước system ready | Deploy chưa hoàn tất | 503 Error, data corruption | Readiness probe | Medium | Implement graceful startup, readiness checks |

## 6. HAZOP cho Software — Các Node điển hình

### Phân chia Node theo Architecture

| Architecture Layer | Typical Nodes | Key Parameters |
|-------------------|---------------|----------------|
| Presentation | UI Components, Forms, Pages | Flow, Quality, Timing, State |
| API Gateway | Routes, Middleware, Auth | Flow, Quantity, Security, Timing |
| Business Logic | Services, Processors, Rules | Sequence, Quality, Composition, State |
| Data Access | Database, Cache, File I/O | Flow, Quantity, Quality, Timing |
| Integration | External APIs, Message Queue | Flow, Timing, Quality, Composition |
| Infrastructure | Server, Network, Storage | Quantity, Timing, State |

## 7. Phân tích HAZOP dự án CleanBox (Project Analysis)

### 7.1 Node 1: Cleanup Service (`features/cleanup/service.py`)

**Design Intent**: CleanupService nhận danh sách directories từ config, lặp qua từng directory, xóa tất cả files và sub-folders bên trong, sau đó empty Recycle Bin. Báo cáo kết quả (files deleted, space freed, errors).

| Guide Word | Parameter | Deviation | Causes | Consequences | Safeguards | Risk (S×L) | Recommendations |
|-----------|-----------|-----------|--------|-------------|------------|:----------:|----------------|
| **NO** | Flow | Không xóa file nào | Directory trống, permission denied toàn bộ | User không giải phóng space | @retry decorator | 3×3=9 | Báo cáo rõ ràng "0 files deleted" + lý do |
| **MORE** | Quantity | Xóa nhiều hơn mong đợi | User thêm folder lớn chứa data quan trọng | Mất dữ liệu | Không có whitelist | 5×3=15 🔴 | System folder whitelist + preview trước cleanup |
| **LESS** | Quality | Xóa không hết (partial) | Files bị lock bởi process khác | Cleanup incomplete | @retry 3 lần | 2×5=10 | Skip locked + report chi tiết |
| **OTHER THAN** | Composition | Xóa sai folder | Config bị corrupt → path sai | Xóa nhầm dữ liệu | Config validation | 5×1=5 | Validate path exists + is expected before delete |
| **AS WELL AS** | Flow | Xóa + side effect | Xóa folder đang được app khác sử dụng | App khác crash | Không có check | 4×2=8 | Check file locks trước khi xóa |
| **REVERSE** | Flow | Cần undo nhưng không thể | User nhận ra xóa nhầm sau khi cleanup | Mất dữ liệu vĩnh viễn | Recycle Bin (partial) | 5×2=10 | Cleanup history + undo mechanism |
| **LATE** | Timing | Cleanup chạy quá lâu | Directory có hàng triệu files | UI timeout, user nghĩ treo | QThread separation | 3×3=9 | Progress bar + cancel button + timeout |
| **EARLY** | Timing | Cleanup trigger trước user sẵn sàng | Tray "Cleanup Now" vô tình click | Xóa không mong muốn | Không có confirm | 4×3=12 🟠 | Confirmation dialog bắt buộc |

### 7.2 Node 2: Storage Monitor (`features/storage_monitor/service.py`)

**Design Intent**: StorageMonitor sử dụng QTimer polling mỗi 60s, kiểm tra dung lượng tất cả drives qua psutil, emit signal low_space_detected khi drive < 10GB threshold. Theo dõi notified_drives để tránh spam.

| Guide Word | Parameter | Deviation | Causes | Consequences | Safeguards | Risk | Recommendations |
|-----------|-----------|-----------|--------|-------------|------------|:----:|----------------|
| **NO** | Flow | Không detect low space | QTimer stop, psutil fail | User không biết sắp hết dung lượng | Không có health check | 4×2=8 | Health check cho timer + fallback |
| **MORE** | Quantity | Quá nhiều notification | Cooldown mechanism fail | User bị spam → tắt app | notified_drives set | 3×3=9 | Per-drive cooldown timer 24h |
| **MORE** | Quantity | Memory tăng dần | psutil objects không release | App OOM sau vài ngày | Không có monitoring | 5×3=15 🔴 | Memory profiling + cleanup mỗi cycle |
| **LESS** | Quality | Đo sai dung lượng | psutil trả về cached data | Thông báo sai | Không có validation | 3×2=6 | Cross-check với os.statvfs |
| **LATE** | Timing | Detect trễ | Polling interval quá dài | User hết space trước khi biết | Default 60s | 3×2=6 | Cho phép user chỉnh interval |
| **OTHER THAN** | State | Drive disconnect giữa scan | USB rút ra khi đang check | Exception / crash | Không có handling | 4×3=12 🟠 | Try/except per drive |

### 7.3 Node 3: Config Manager (`shared/config/manager.py`)

**Design Intent**: ConfigManager đọc/ghi config.json tại %APPDATA%\.cleanbox\. Load config khi khởi động, save mỗi khi user thay đổi settings. Merge với default values cho missing keys.

| Guide Word | Parameter | Deviation | Causes | Consequences | Safeguards | Risk | Recommendations |
|-----------|-----------|-----------|--------|-------------|------------|:----:|----------------|
| **NO** | Flow | Không save được | Permission denied, disk full | Thay đổi mất khi restart | Basic error handling | 4×2=8 | Retry + notify user + log |
| **PART OF** | Composition | Save thiếu fields | Code bug, partial update | Config inconsistent | Default merge | 3×2=6 | Schema validation trước save |
| **REVERSE** | Flow | Load config sai version | Format thay đổi sau upgrade | App crash hoặc sai behavior | Version check | 5×2=10 | Config migration + versioning |
| **OTHER THAN** | Quality | JSON invalid | Power loss during write | App reset to defaults | JSON parse error handling | 4×2=8 | Atomic write + backup |

### 7.4 Node 4: System Tray (`ui/tray_icon.py`)

**Design Intent**: TrayIcon chạy trong separate thread (pystray), hiển thị icon trong system tray, menu gồm: Cleanup Now, Open Settings, Exit. Callbacks emit signals an toàn qua _emit_*() methods.

| Guide Word | Parameter | Deviation | Causes | Consequences | Safeguards | Risk | Recommendations |
|-----------|-----------|-----------|--------|-------------|------------|:----:|----------------|
| **NO** | Flow | Icon biến mất | pystray thread crash | User không tương tác được | Separate thread | 4×2=8 | Auto-restart tray thread + health check |
| **AS WELL AS** | Security | Menu bị inject | pystray vulnerability | Unauthorized action | N/A (pystray managed) | 5×1=5 | Keep pystray updated |
| **EARLY** | Timing | Menu callback trước app ready | Race condition startup | NoneType error, crash | Không có ready check | 4×2=8 | Check app.is_ready trước callback |

### 7.5 HAZOP Findings Summary

| Priority | Count | Deviations |
|----------|-------|-----------|
| 🔴 Critical (15+) | 2 | MORE/Quantity cleanup, MORE/Quantity memory |
| 🟠 High (10-14) | 3 | EARLY/Timing cleanup, REVERSE/Flow cleanup, OTHER THAN/State drive |
| 🟡 Medium (6-9) | 8 | Various |
| 🟢 Low (1-5) | 3 | Various |

## 8. Kế hoạch triển khai và xác minh HAZOP (Implementation & Verification Plan)

### 8.1 Critical Deviations Action Plan

| Node | Deviation | Guide Word | Action | Implementation | Verification |
|------|-----------|-----------|--------|---------------|-------------|
| Cleanup | MORE/Quantity (xóa quá nhiều) | MORE | Whitelist + Preview + Confirm | `PROTECTED_PATHS` in constants.py; QMessageBox preview | Unit: whitelist blocks; E2E: confirm flow |
| Storage | MORE/Quantity (memory leak) | MORE | Memory cleanup per cycle | `del` objects + periodic `gc.collect()` | Integration: 10K cycles < 10MB delta |
| Cleanup | EARLY/Timing (vô tình trigger) | EARLY | Mandatory confirmation | QMessageBox.warning before cleanup | E2E: no cleanup without confirm |
| Storage | OTHER THAN/State (drive disconnect) | OTHER THAN | Per-drive try/except | Wrap each drive check in try/except | Unit: mock removed drive → graceful |
| Cleanup | REVERSE/Flow (need undo) | REVERSE | Cleanup history + undo | Save manifest to cleanup_history/ | Integration: undo restores files |

### 8.2 HAZOP Verification Matrix

| Node | Unit Test | Integration Test | E2E Test | Manual Test |
|------|-----------|-----------------|----------|-------------|
| Cleanup Service | ✅ Whitelist, retry, skip locked | ✅ Full cleanup + report | ✅ User flow with confirm | ✅ Large directory |
| Storage Monitor | ✅ Mock psutil responses | ✅ Memory profiling 10K cycles | — | ✅ USB hot-unplug |
| Config Manager | ✅ Atomic write, schema validation | ✅ Crash during write | — | ✅ Manual config edit |
| System Tray | ✅ Mock pystray callbacks | ✅ Tray crash → restart | — | ✅ Visual tray behavior |

### 8.3 HAZOP Re-study Triggers

| Trigger | Action |
|---------|--------|
| New feature added | HAZOP cho node mới / affected nodes |
| Major architecture change | Full HAZOP re-study |
| Production incident | Targeted HAZOP cho node liên quan |
| Dependency major upgrade | HAZOP cho integration nodes |
| Mỗi 2 releases | Periodic HAZOP review |

## 9. So sánh HAZOP vs FMEA

| Aspect | HAZOP | FMEA |
|--------|-------|------|
| Approach | Guide words + parameters | Failure modes |
| Team size | 5-7 (workshop) | 3-5 (có thể nhỏ hơn) |
| Focus | Deviations from design intent | Component failure modes |
| Output | Recommendations | RPN ranking |
| Time investment | High (workshops) | Medium |
| Best for | Complex interactions, new designs | Individual component analysis |
| Complementary | Dùng trước FMEA | Dùng sau HAZOP |

## 10. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Phân tích có cấu trúc, hệ thống (guide words đảm bảo coverage)
- ✅ Team-based → đa góc nhìn, phát hiện nhiều vấn đề hơn
- ✅ Phát hiện được operability issues (không chỉ safety)
- ✅ Áp dụng được cho mọi giai đoạn (design, development, operation)
- ✅ Tạo tài liệu chi tiết, có giá trị tham khảo lâu dài

### Hạn chế
- ❌ Tốn thời gian (cần nhiều workshops)
- ❌ Phụ thuộc vào chất lượng team và Study Leader
- ❌ Có thể bỏ sót nếu guide words không đủ
- ❌ Không tính định lượng probability (cần kết hợp phương pháp khác)
- ❌ Khó áp dụng cho hệ thống rất lớn nếu không chia node tốt

## 11. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| IEC 61882:2016 | Hazard and operability studies (HAZOP studies) — Application guide |
| ISO 31010:2019 | Risk assessment techniques |
| BS EN 61882 | HAZOP standard (European) |
| IEC 61508 | Functional safety — recommends HAZOP |

## 12. Tài liệu tham khảo

1. IEC 61882:2016 - Hazard and operability studies (HAZOP studies) — Application guide
2. Kletz, T. (1999) - "HAZOP and HAZAN: Identifying and Assessing Process Industry Hazards"
3. Crawley, F. & Tyler, B. (2015) - "HAZOP: Guide to Best Practice"
4. Redmill, F. et al. (1999) - "System Safety: HAZOP and Software HAZOP"
5. Fencott, C. (1998) - "Applying Formal Methods to Software HAZOP"
