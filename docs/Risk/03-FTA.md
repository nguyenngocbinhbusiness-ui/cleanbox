# FTA (Fault Tree Analysis)

## 1. Tổng quan (Overview)

**FTA** (Fault Tree Analysis — Phân tích cây lỗi) là phương pháp phân tích rủi ro **top-down, deductive** (suy diễn từ trên xuống), bắt đầu từ một **sự kiện không mong muốn** (Top Event / Undesired Event) và truy ngược về các **nguyên nhân gốc rễ** thông qua cấu trúc cây logic.

FTA sử dụng **logic gates** (AND, OR) để mô tả mối quan hệ nhân quả giữa các sự kiện, cho phép:
- Xác định **tất cả** các tổ hợp nguyên nhân dẫn đến sự cố
- Tính xác suất xảy ra sự cố
- Tìm **Minimal Cut Sets** (tập nguyên nhân tối thiểu)

## 2. Các thành phần của Fault Tree

### 2.1 Ký hiệu sự kiện (Event Symbols)

| Ký hiệu | Tên | Mô tả |
|----------|-----|-------|
| ▭ (Rectangle) | Intermediate Event | Sự kiện trung gian, có thể phân tích sâu hơn |
| ○ (Circle) | Basic Event | Sự kiện cơ bản (lá), không phân tích thêm |
| ◇ (Diamond) | Undeveloped Event | Sự kiện chưa phân tích (thiếu thông tin) |
| ⌂ (House) | External Event | Sự kiện bên ngoài, điều kiện biên |
| △ (Triangle) | Transfer | Nối sang trang/nhánh khác |

### 2.2 Logic Gates

| Gate | Ký hiệu | Ý nghĩa | Mô tả |
|------|----------|---------|-------|
| AND Gate | ∧ | VÀ | Top event xảy ra khi **TẤT CẢ** input events đồng thời xảy ra |
| OR Gate | ∨ | HOẶC | Top event xảy ra khi **BẤT KỲ** input event nào xảy ra |
| Exclusive OR | ⊕ | XOR | Top event xảy ra khi **ĐÚNG MỘT** input event xảy ra |
| Priority AND | P-AND | Ưu tiên | Như AND nhưng input phải xảy ra theo **thứ tự** nhất định |
| Inhibit Gate | ⊳ | Điều kiện | Output xảy ra khi input xảy ra VÀ điều kiện được thỏa mãn |

## 3. Quy trình xây dựng Fault Tree

### Bước 1: Xác định Top Event
- Chọn sự kiện không mong muốn cần phân tích
- Định nghĩa rõ ràng, cụ thể
- Ví dụ: "Hệ thống mất dữ liệu người dùng"

### Bước 2: Xác định phạm vi và ranh giới
- System boundary (ranh giới hệ thống)
- Assumptions (giả định)
- Resolution level (mức chi tiết)

### Bước 3: Xây dựng cây lỗi
- Từ Top Event, đặt câu hỏi: "Sự kiện này xảy ra do đâu?"
- Xác định immediate causes (nguyên nhân trực tiếp)
- Chọn logic gate phù hợp (AND/OR)
- Tiếp tục phân tích sâu cho đến Basic Events

### Bước 4: Phân tích định tính (Qualitative Analysis)
- Tìm **Minimal Cut Sets** (MCS)
- Tìm **Common Cause Failures**
- Xác định **Single Points of Failure**

### Bước 5: Phân tích định lượng (Quantitative Analysis)
- Gán xác suất cho Basic Events
- Tính xác suất Top Event
- **OR gate**: P(A ∨ B) = P(A) + P(B) - P(A)·P(B) ≈ P(A) + P(B) (khi P nhỏ)
- **AND gate**: P(A ∧ B) = P(A) · P(B) (khi độc lập)

## 4. Minimal Cut Sets (MCS)

### Định nghĩa
**Minimal Cut Set** là tập hợp nhỏ nhất các Basic Events mà khi tất cả đồng thời xảy ra sẽ dẫn đến Top Event.

### Ý nghĩa
- **Cut set 1 phần tử** → Single Point of Failure (rủi ro cao nhất)
- **Cut set nhiều phần tử** → Cần nhiều sự kiện đồng thời (an toàn hơn)

### Cách tìm MCS
1. Biểu diễn Fault Tree dưới dạng Boolean algebra
2. Áp dụng các quy tắc đại số Boolean
3. Rút gọn để tìm MCS

## 5. Ví dụ: FTA cho phần mềm

### Top Event: "Mất dữ liệu người dùng"

```
                    ┌──────────────────────┐
                    │   Mất dữ liệu        │
                    │   người dùng          │
                    │   (Top Event)         │
                    └──────────┬───────────┘
                               │
                          ┌────┴────┐
                          │   OR    │
                          └────┬────┘
                    ┌──────────┼──────────┐
                    │          │          │
            ┌───────┴──┐ ┌────┴─────┐ ┌──┴────────┐
            │ Database  │ │ Backup   │ │ Software  │
            │ Failure   │ │ Failure  │ │ Bug       │
            └─────┬─────┘ └────┬─────┘ └─────┬─────┘
                  │            │              │
             ┌────┴────┐  ┌───┴────┐    ┌────┴────┐
             │   OR    │  │  AND   │    │   OR    │
             └────┬────┘  └───┬────┘    └────┬────┘
            ┌─────┼─────┐  ┌──┼───┐    ┌────┼─────┐
            │     │     │  │  │   │    │    │     │
           ○HW  ○Corr ○Cfg ○BF ○RS  ○Del ○Over ○Race
           Fail  upt   Err  ail  tor   ete  writ  Cond
                               age     API  e Bug
                               Fail
```

**Legend:**
- ○ HW Fail: Hardware failure (disk crash)
- ○ Corrupt: Database corruption
- ○ Cfg Err: Configuration error (wrong connection string)
- ○ BFail: Backup process failure
- ○ RStorage Fail: Remote storage unavailable
- ○ Delete API: Accidental delete via API
- ○ Overwrite Bug: Data overwrite bug in code
- ○ Race Cond: Race condition causing data loss

### Minimal Cut Sets phân tích:
- **MCS1**: {HW Fail} — Single Point of Failure!
- **MCS2**: {Corrupt}
- **MCS3**: {Cfg Err}
- **MCS4**: {BFail, RStorage Fail} — cần cả hai mới fail
- **MCS5**: {Delete API}
- **MCS6**: {Overwrite Bug}
- **MCS7**: {Race Cond}

→ Nhiều Single Points of Failure → cần thêm redundancy

## 6. Phân tích định lượng

### Ví dụ tính xác suất

| Basic Event | Probability |
|-------------|------------|
| HW Fail | 0.001 |
| Corrupt | 0.0005 |
| Cfg Err | 0.002 |
| BFail | 0.01 |
| RStorage Fail | 0.005 |
| Delete API | 0.0001 |
| Overwrite Bug | 0.0003 |
| Race Cond | 0.0002 |

```
P(Database Failure) = 1 - (1-0.001)(1-0.0005)(1-0.002)
                    ≈ 0.001 + 0.0005 + 0.002 = 0.0035

P(Backup Failure)   = 0.01 × 0.005 = 0.00005

P(Software Bug)     = 1 - (1-0.0001)(1-0.0003)(1-0.0002)
                    ≈ 0.0001 + 0.0003 + 0.0002 = 0.0006

P(Top Event)        ≈ 0.0035 + 0.00005 + 0.0006 = 0.00415
                    ≈ 0.42%
```

## 7. Phân tích FTA dự án CleanBox (Project Analysis)

### 7.1 Top Event: "Người dùng mất dữ liệu do CleanBox"

```
                        ┌──────────────────────────────┐
                        │     USER DATA LOSS            │
                        │     do CleanBox               │
                        │     (Top Event)               │
                        └──────────────┬───────────────┘
                                       │
                                  ┌────┴────┐
                                  │   OR    │
                                  └────┬────┘
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
           ┌────────┴───────┐  ┌──────┴───────┐  ┌──────┴────────┐
           │ Cleanup xóa    │  │ Config data  │  │ Silent data   │
           │ nhầm files     │  │ loss         │  │ corruption    │
           └───────┬────────┘  └──────┬───────┘  └──────┬────────┘
                   │                  │                  │
              ┌────┴────┐        ┌────┴────┐        ┌───┴────┐
              │   OR    │        │   OR    │        │  AND   │
              └────┬────┘        └────┬────┘        └───┬────┘
         ┌────────┼────────┐    ┌────┼────┐       ┌────┼────┐
         │        │        │    │    │    │       │    │    │
        ○A1     ○A2      ○A3  ○B1  ○B2  ○B3    ○C1  ○C2  ○C3
```

**Basic Events — Nhánh 1: Cleanup xóa nhầm files**

| ID | Basic Event | Mô tả | P (probability) |
|----|------------|-------|-----------------|
| A1 | User thêm thư mục quan trọng | User vô tình thêm Documents, Desktop vào cleanup list | 0.05 |
| A2 | Không có confirmation | Cleanup chạy không có dialog xác nhận | 0.8 (hiện tại!) |
| A3 | Tray cleanup auto-trigger | User click "Cleanup Now" từ tray không thấy preview | 0.3 |

**Basic Events — Nhánh 2: Config data loss**

| ID | Basic Event | Mô tả | P |
|----|------------|-------|---|
| B1 | Config file corrupt | JSON write bị interrupt → file rỗng/invalid | 0.01 |
| B2 | Config path deleted | %APPDATA%\.cleanbox bị xóa bởi cleanup tool khác | 0.005 |
| B3 | Permission denied | File system permission thay đổi | 0.002 |

**Basic Events — Nhánh 3: Silent data corruption**

| ID | Basic Event | Mô tả | P |
|----|------------|-------|---|
| C1 | Race condition | CleanupWorker + ConfigManager truy cập đồng thời | 0.02 |
| C2 | Partial cleanup | Cleanup bị interrupt giữa chừng | 0.05 |
| C3 | No error reporting | Lỗi xảy ra nhưng không thông báo user | 0.1 |

### 7.2 Tính xác suất Top Event

```
P(Cleanup xóa nhầm) = 1 - (1-0.05)(1-0.8)(1-0.3)
                     ≈ 0.05 + 0.8 + 0.3 - overlaps
                     = 1 - (0.95)(0.2)(0.7) = 1 - 0.133 = 0.867
                     ⚠️ RẤT CAO vì A2 (no confirmation) = 0.8

P(Config loss)       = 1 - (1-0.01)(1-0.005)(1-0.002)
                     ≈ 0.01 + 0.005 + 0.002 = 0.017

P(Silent corruption) = 0.02 × 0.05 × 0.1 = 0.0001 (cần cả 3 AND)

P(Top Event)         ≈ 1 - (1-0.867)(1-0.017)(1-0.0001)
                     ≈ 0.869
```

### 7.3 Minimal Cut Sets

| MCS # | Basic Events | Order | Probability | Criticality |
|-------|-------------|-------|------------|-------------|
| MCS-1 | {A2} — No confirmation dialog | 1 | 0.80 | 🔴 CRITICAL — Single Point of Failure |
| MCS-2 | {A3} — Tray auto-trigger no preview | 1 | 0.30 | 🔴 HIGH |
| MCS-3 | {A1} — User thêm folder quan trọng | 1 | 0.05 | 🟠 MEDIUM |
| MCS-4 | {B1} — Config corrupt | 1 | 0.01 | 🟡 LOW |
| MCS-5 | {C1, C2, C3} — Silent corruption | 3 | 0.0001 | 🟢 VERY LOW |

### 7.4 Key Findings

1. **A2 (No confirmation)** là Single Point of Failure nghiêm trọng nhất — P = 0.8
2. **A3 (Tray cleanup)** không có preview → user dễ trigger nhầm
3. **Config corruption** (B1-B3) rủi ro thấp nhưng impact cao
4. **Silent corruption** (C1-C3) yêu cầu 3 events đồng thời → rủi ro thấp

### 7.5 Top Event 2: "Application Crash / Unresponsive"

```
                    ┌────────────────────────────┐
                    │   App Crash / Unresponsive  │
                    │   (Top Event 2)             │
                    └─────────────┬──────────────┘
                                  │
                             ┌────┴────┐
                             │   OR    │
                             └────┬────┘
                ┌─────────────────┼─────────────────┐
                │                 │                 │
         ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
         │ Memory      │  │ Thread      │  │ External    │
         │ Exhaustion  │  │ Deadlock    │  │ API Fail    │
         └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                │                │                 │
           ┌────┴────┐     ┌────┴────┐       ┌────┴────┐
           │   OR    │     │  AND    │       │   OR    │
           └────┬────┘     └────┬────┘       └────┬────┘
          ┌─────┼─────┐   ┌────┼────┐     ┌─────┼─────┐
         ○D1  ○D2   ○D3  ○E1  ○E2       ○F1   ○F2   ○F3
```

| ID | Event | P |
|----|-------|---|
| D1 | StorageMonitor memory leak | 0.05 |
| D2 | FolderScanner OOM trên ổ lớn | 0.03 |
| D3 | Notification queue overflow | 0.01 |
| E1 | QThread không release lock | 0.01 |
| E2 | ConfigManager concurrent access | 0.02 |
| F1 | winshell API crash | 0.02 |
| F2 | pystray thread crash | 0.03 |
| F3 | psutil stale partition error | 0.02 |

## 8. Kế hoạch triển khai và xác minh FTA (Implementation & Verification Plan)

### 8.1 Biện pháp cho từng Single Point of Failure

| MCS | Basic Event | Mitigation | Verification |
|-----|------------|-----------|-------------|
| MCS-1 | A2: No confirmation | Thêm QMessageBox.warning trước mỗi cleanup | E2E test: cleanup → dialog appears → cancel/confirm works |
| MCS-2 | A3: Tray no preview | Thêm summary popup trước tray cleanup | Manual test: tray "Cleanup Now" → preview dialog → confirm |
| MCS-1+2 | Combined | Thêm PROTECTED_PATHS whitelist (Windows, System32, Program Files) | Unit test: protected paths → raise ProtectedPathError |
| MCS-4 | B1: Config corrupt | Atomic write + backup file | Unit test: simulate write interrupt → backup restores |

### 8.2 Post-Mitigation Probability Targets

| Basic Event | Current P | Target P (After Mitigation) | Method |
|------------|-----------|---------------------------|--------|
| A2 (No confirmation) | 0.80 | 0.02 | Confirmation dialog |
| A3 (Tray no preview) | 0.30 | 0.05 | Preview summary |
| A1 (Add important folder) | 0.05 | 0.005 | Whitelist + warning |
| B1 (Config corrupt) | 0.01 | 0.001 | Atomic write |
| **P(Top Event) target** | **0.869** | **< 0.05** | |

### 8.3 Verification Plan

| Phase | Activity | Tool | Success Criteria |
|-------|----------|------|-----------------|
| Development | Implement confirmation dialog | PyQt6 QMessageBox | Dialog shown before every destructive action |
| Unit Test | Test whitelist protection | pytest + mock | 100% protected paths blocked |
| Integration | Test full cleanup flow | pytest-qt | Cleanup → confirm → execute → report |
| Regression | Prevent bypasses | CI/CD GitHub Actions | No cleanup without confirmation in any code path |
| Monitoring | Log all cleanup actions | Python logging | Audit trail cho mỗi file/folder deleted |

## 9. FTA cho phần mềm — Đặc thù

### 7.1 Loại lỗi phần mềm thường phân tích
- Logic errors trong business rules
- Exception handling failures
- Concurrency issues (deadlock, race conditions)
- Integration failures (API, database, external services)
- Configuration/deployment errors
- Security vulnerabilities

### 7.2 Kết hợp FTA với phương pháp khác
| Kết hợp | Mục đích |
|---------|---------|
| FTA + FMEA | FTA tìm cause, FMEA đánh giá từng failure mode |
| FTA + ETA | FTA phân tích cause, ETA phân tích consequence |
| FTA + Risk Matrix | Ưu tiên hóa dựa trên probability từ FTA |

## 10. Template FTA Report

### 8.1 Header

| Field | Value |
|-------|-------|
| Project | [Tên dự án] |
| System/Component | [Hệ thống phân tích] |
| Top Event | [Sự kiện không mong muốn] |
| Analyst | [Người phân tích] |
| Date | [Ngày thực hiện] |
| Revision | [Phiên bản] |

### 8.2 Summary Table

| MCS # | Basic Events | Probability | Order | Criticality |
|-------|-------------|------------|-------|-------------|
| MCS-1 | [Events] | [P] | [Số phần tử] | [High/Med/Low] |

## 11. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Phân tích top-down trực quan
- ✅ Xác định được tất cả tổ hợp nguyên nhân
- ✅ Tính được xác suất sự cố
- ✅ Tìm được Single Points of Failure
- ✅ Phù hợp cho phân tích safety-critical systems

### Hạn chế
- ❌ Chỉ phân tích một Top Event tại một thời điểm
- ❌ Phức tạp cho hệ thống lớn
- ❌ Khó xử lý feedback loops và time-dependent failures
- ❌ Yêu cầu hiểu sâu về hệ thống
- ❌ Binary logic (fail/success) — không mô hình hóa partial failures

## 12. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| IEC 61025:2006 | Fault tree analysis (FTA) |
| ISO 31010:2019 | Risk assessment techniques |
| NASA Fault Tree Handbook (NUREG-0492) | Handbook toàn diện về FTA |
| IEC 61508 | Functional safety |

## 13. Tài liệu tham khảo

1. IEC 61025:2006 - Fault tree analysis (FTA)
2. Vesely, W.E. et al. (1981) - "Fault Tree Handbook" (NUREG-0492)
3. Ericson, C.A. (2005) - "Hazard Analysis Techniques for System Safety"
4. Stamatelatos, M. et al. (2002) - "Fault Tree Handbook with Aerospace Applications" (NASA)
5. Leveson, N. (2012) - "Engineering a Safer World" (MIT Press)
