# ETA (Event Tree Analysis)

## 1. Tổng quan (Overview)

**ETA** (Event Tree Analysis — Phân tích cây sự kiện) là phương pháp phân tích rủi ro **bottom-up, inductive** (quy nạp từ dưới lên), bắt đầu từ một **Initiating Event** (sự kiện khởi phát) và phân tích chuỗi các **hậu quả** có thể xảy ra dựa trên sự thành công/thất bại của các **safety barriers** (rào cản an toàn).

ETA là phương pháp **bổ sung cho FTA** — trong khi FTA đi từ hậu quả ngược về nguyên nhân, ETA đi từ nguyên nhân tiến về các hậu quả có thể.

### Đặc điểm chính
- **Forward logic**: Đi theo chiều thuận thời gian
- **Binary branching**: Mỗi barrier có 2 nhánh (success / failure)
- **Scenario identification**: Xác định tất cả kịch bản có thể
- **Probability calculation**: Tính xác suất từng outcome

## 2. Cấu trúc Event Tree

### 2.1 Các thành phần

| Thành phần | Mô tả | Vị trí |
|-----------|-------|--------|
| Initiating Event | Sự kiện khởi phát (trigger) | Bên trái |
| Safety Barriers / Pivotal Events | Các rào cản/biện pháp an toàn | Cột header |
| Branches | Nhánh success (lên) / failure (xuống) | Thân cây |
| End States / Outcomes | Kết quả cuối cùng của mỗi kịch bản | Bên phải |
| Probabilities | Xác suất tại mỗi nhánh | Trên nhánh |

### 2.2 Cấu trúc tổng quát

```
Initiating     Barrier 1    Barrier 2    Barrier 3     Outcome
Event          (Success/    (Success/    (Success/
               Failure)     Failure)     Failure)
                  │            │            │
    ┌─────────────┤            │            │
    │         Success──────Success──────Success ──→ O1: Safe (P1)
    │             │            │
    │             │        Success──────Failure ──→ O2: Minor (P2)
    │             │
IE ─┤         Success──────Failure──────Success ──→ O3: Moderate (P3)
    │             │            │
    │             │        Failure──────Failure ──→ O4: Serious (P4)
    │             │
    │         Failure──────Success──────Success ──→ O5: Moderate (P5)
    │             │            │
    │             │        Success──────Failure ──→ O6: Serious (P6)
    │             │
    │         Failure──────Failure──────Success ──→ O7: Critical (P7)
    │             │
    └─────────────┘        Failure──────Failure ──→ O8: Catastrophic (P8)
```

## 3. Quy trình thực hiện ETA

### Bước 1: Xác định Initiating Event
- Sự kiện bất thường có thể gây ra hậu quả
- Ví dụ: Server crash, data corruption, security breach attempt
- Nguồn: từ FMEA, FTA, incident history

### Bước 2: Xác định Safety Barriers
- Liệt kê các rào cản/biện pháp an toàn theo **thứ tự thời gian**
- Mỗi barrier phải là binary (hoạt động / không hoạt động)
- Ví dụ: Failover system, backup restore, monitoring alert

### Bước 3: Xây dựng Event Tree
- Vẽ từ trái sang phải
- Mỗi barrier tạo 2 nhánh: Success (lên) / Failure (xuống)
- Với n barriers → tối đa 2^n outcomes

### Bước 4: Phân loại Outcomes
- Gán mức severity cho mỗi outcome
- Phân loại: Safe / Minor / Moderate / Serious / Catastrophic

### Bước 5: Gán xác suất
- P(Initiating Event): từ historical data, FMEA
- P(Barrier Success/Failure): từ reliability data, FTA
- P(Outcome) = P(IE) × P(Branch₁) × P(Branch₂) × ... × P(Branchₙ)

### Bước 6: Phân tích kết quả
- Tổng xác suất tất cả outcomes = P(IE)
- Xác định outcomes có rủi ro cao nhất
- Đề xuất cải thiện barriers yếu

## 4. Ví dụ: ETA cho phần mềm — Database Server Crash

### Initiating Event: Database Server Crash

| IE | Auto Failover | Backup Restore | Manual Recovery | Outcome | Severity | Probability |
|----|---------------|---------------|-----------------|---------|----------|-------------|
| DB Crash | ✅ Success | — | — | O1: No downtime, auto switch | Negligible | 0.01 × 0.95 = 0.0095 |
| (P=0.01) | ❌ Failure | ✅ Success | — | O2: Short downtime (~30min) | Minor | 0.01 × 0.05 × 0.90 = 0.00045 |
| | ❌ Failure | ❌ Failure | ✅ Success | O3: Extended downtime (hours) | Moderate | 0.01 × 0.05 × 0.10 × 0.80 = 0.00004 |
| | ❌ Failure | ❌ Failure | ❌ Failure | O4: Data loss, prolonged outage | Critical | 0.01 × 0.05 × 0.10 × 0.20 = 0.00001 |

### Phân tích
- **O1** (Auto Failover thành công): 95% → Rủi ro thấp ✅
- **O4** (Mọi barrier đều fail): 0.001% → Rất hiếm nhưng impact cực cao ⚠️
- **Barrier yếu nhất**: Manual Recovery (80% success) → cần cải thiện
- **Tổng P(outcomes)** = 0.0095 + 0.00045 + 0.00004 + 0.00001 = 0.01 ✓

## 5. Ví dụ: ETA cho Security Breach Attempt

### Initiating Event: Unauthorized Access Attempt

```
IE: Unauthorized    Firewall/    Auth        Rate        Alert &     Outcome
Access Attempt      WAF          System      Limiting    Response
(P = 0.1/day)
                    │
              ┌─ Blocked ───────────────────────────────→ O1: No impact
              │   (0.85)                                   P = 0.085
              │
              │         ┌─ Auth Reject ─────────────────→ O2: Logged attempt
              │         │   (0.95)                         P = 0.01425
              │         │
              ├─ Pass ──┤         ┌─ Limited ───────────→ O3: Limited exposure
              │  (0.15) │         │   (0.90)               P = 0.000675
              │         │         │
              │         └─ Auth ──┤        ┌─ Detected ─→ O4: Breach contained
              │           Bypass  │        │   (0.80)      P = 0.00006
              │           (0.05)  │        │
              │                   └─ Not ──┤
              │                     Limit  └─ Missed ───→ O5: Full breach
              │                     (0.10)    (0.20)       P = 0.000015
              │                                            ⚠️ CRITICAL
```

## 7. Phân tích ETA dự án CleanBox (Project Analysis)

### 7.1 Initiating Event 1: User click "Cleanup Now"

| IE | Confirmation Dialog | Path Validation | File Delete Success | Notification | Outcome | Severity | Probability |
|----|-------------------|----------------|--------------------|--------------|---------|---------:|------------:|
| Cleanup | ✅ Confirmed | ✅ Valid paths | ✅ All deleted | ✅ Toast shown | **O1**: Successful cleanup | Negligible | 0.70 |
| Triggered | ✅ Confirmed | ✅ Valid paths | ✅ All deleted | ❌ Toast fails | **O2**: Cleanup OK, no notification | Minor | 0.05 |
| (P=1.0 | ✅ Confirmed | ✅ Valid paths | ❌ Some locked | ✅ Toast shown | **O3**: Partial cleanup + report | Minor | 0.10 |
| per action) | ✅ Confirmed | ❌ Invalid paths | — | ✅ Error shown | **O4**: Cleanup aborted, user informed | Moderate | 0.05 |
| | ✅ Confirmed | ✅ Valid paths | ❌ Permission denied | ❌ No feedback | **O5**: Silent failure | Major | 0.02 |
| | ❌ Cancelled | — | — | — | **O6**: No action (safe) | Negligible | 0.08 |

**Key Findings:**
- **O5 (Silent failure)** là worst case: cleanup fail nhưng user không biết → P = 0.02
- **O1 (Happy path)** chiếm 70% → hệ thống ổn định
- **Barrier yếu nhất**: Notification service (win11toast) — nếu fail → user mất feedback

### 7.2 Initiating Event 2: Drive space < threshold

| IE | StorageMonitor detects | Cooldown check | Toast notification | User action | Outcome | Severity | Probability |
|----|----------------------|----------------|-------------------|-----------|---------|---------:|------------:|
| Low space | ✅ Detected | ✅ First alert | ✅ Toast shown | ✅ User cleans up | **O1**: Space freed | Negligible | 0.50 |
| (P=0.3 | ✅ Detected | ✅ First alert | ✅ Toast shown | ❌ User ignores | **O2**: Space remains low | Minor | 0.20 |
| per month) | ✅ Detected | ❌ Already notified | — | — | **O3**: Silent (cooldown) | Negligible | 0.15 |
| | ✅ Detected | ✅ First alert | ❌ Toast fails | — | **O4**: Low space unnoticed | Moderate | 0.03 |
| | ❌ Not detected | — | — | — | **O5**: Monitoring failure | Major | 0.01 |
| | ✅ Detected | ❌ Spam (no cooldown) | ✅✅✅ Many toasts | ❌ User disables app | **O6**: User disables CleanBox | Moderate | 0.05 |

**Key Findings:**
- **O5 (Monitoring failure)** hiếm (P=0.01) nhưng đánh bại mục đích core
- **O6 (Notification spam)** → user tắt app = mất hoàn toàn protection
- notified_drives mechanism là barrier quan trọng (ngăn spam)

### 7.3 Initiating Event 3: Application Startup

| IE | Single Instance Check | Config Load | Storage Monitor Start | Tray Icon Init | Outcome | Severity | Probability |
|----|---------------------|-------------|----------------------|---------------|---------|----------|-------------|
| App Start | ✅ No other instance | ✅ Config valid | ✅ Monitor running | ✅ Tray visible | **O1**: Normal startup | Negligible | 0.85 |
| (P=1.0 | ✅ No other instance | ✅ Config valid | ✅ Monitor running | ❌ Tray crash | **O2**: App runs but no tray | Moderate | 0.03 |
| per boot) | ✅ No other instance | ❌ Config corrupt | ✅ Defaults used | ✅ Tray visible | **O3**: Reset to defaults | Minor | 0.02 |
| | ❌ Already running | — | — | — | **O4**: Second instance blocked | Negligible | 0.05 |
| | ❌ Stale lock | — | — | — | **O5**: App won't start | Major | 0.01 |
| | ✅ No other instance | ❌ Config unreadable | ❌ Monitor fails | ❌ Tray fails | **O6**: Complete startup failure | Critical | 0.001 |

### 7.4 Barrier Effectiveness Summary

| Barrier | Applied To | P(Success) | Effectiveness | Improvement Needed |
|---------|-----------|------------|---------------|-------------------|
| Confirmation Dialog | Cleanup IE | 0.92 | ✅ Strong (sau khi implement) | N/A |
| Path Validation | Cleanup IE | 0.95 | ✅ Strong | Add whitelist |
| File Delete + Retry | Cleanup IE | 0.80 | ⚠️ Moderate | Improve retry logic |
| Toast Notification | Multiple IEs | 0.90 | ⚠️ Moderate | Fallback notification |
| Cooldown Mechanism | Low Space IE | 0.85 | ⚠️ Moderate | Per-drive timer |
| Config Validation | Startup IE | 0.95 | ✅ Strong | Add schema validation |
| Single Instance Lock | Startup IE | 0.94 | ⚠️ Moderate | Stale lock detection |
| Tray Icon Thread | Startup IE | 0.95 | ✅ Strong | Auto-restart on crash |

## 8. Kế hoạch triển khai và xác minh ETA (Implementation & Verification Plan)

### 8.1 Barrier Improvements

| # | Barrier | Current P(Fail) | Target P(Fail) | Implementation | Verification |
|---|---------|----------------|----------------|---------------|-------------|
| 1 | File Delete Retry | 0.20 | 0.05 | Improve @retry decorator: 3 attempts, exponential backoff, skip locked files | Integration test: mock locked files → retry → skip → report |
| 2 | Toast Fallback | 0.10 | 0.02 | If win11toast fails → fallback to QSystemTrayIcon.showMessage() | Unit test: mock toast failure → fallback triggers |
| 3 | Cooldown Timer | 0.15 | 0.05 | Per-drive cooldown 24h timer (hiện tại chỉ track set) | Unit test: same drive alert within 24h → suppressed |
| 4 | Stale Lock Detection | 0.06 | 0.01 | Check lock age > 5min → delete stale lock | Unit test: create stale lock → app starts normally |
| 5 | Tray Auto-restart | 0.05 | 0.01 | Monitor pystray thread health, restart on crash | Integration test: kill tray thread → auto-restart within 5s |

### 8.2 Scenario-Based Test Plan

| IE | Scenario | Test Type | Steps | Expected Outcome |
|----|----------|-----------|-------|-----------------|
| Cleanup | O1: Happy path | E2E | Add dir → click cleanup → confirm → verify deleted | Files removed, toast shown |
| Cleanup | O3: Partial cleanup | Integration | Lock some files → cleanup → verify partial | Unlocked files removed, locked skipped, report shown |
| Cleanup | O5: Silent failure | Integration | Mock all permissions denied → verify notification | Error notification shown (not silent) |
| Low Space | O4: Toast fails | Unit | Mock win11toast error → verify fallback | QSystemTrayIcon message shown |
| Low Space | O6: Spam prevention | Unit | Trigger same drive alert 5× → count notifications | Only 1 notification per 24h |
| Startup | O5: Stale lock | Unit | Create stale lock file → start app → verify | App starts, stale lock removed |
| Startup | O6: Complete failure | Integration | Corrupt config + mock failures → verify | Graceful error message, not crash |

### 8.3 Metrics & Acceptance Criteria

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| P(Successful Cleanup) = O1 | ~70% | > 90% | Track cleanup results in logs |
| P(Silent Failure) | ~2% | < 0.1% | Monitor unhandled exceptions |
| P(Startup Success) | ~85% | > 98% | Track startup failures in logs |
| Barrier test coverage | — | 100% | pytest-cov for barrier code paths |

## 9. Kết hợp ETA với FTA (Bow-tie)

ETA và FTA thường được kết hợp thành **Bow-tie Analysis**:

```
     FTA (Causes)          │  Event  │        ETA (Consequences)
                           │         │
  Cause 1 ──┐              │         │              ┌── Outcome 1
             ├── AND ──┐   │         │   ┌── B1 ───┤
  Cause 2 ──┘          │   │         │   │          └── Outcome 2
                        ├───│ Hazard  │───┤
  Cause 3 ──┐          │   │  Event  │   │          ┌── Outcome 3
             ├── OR ───┘   │         │   └── B2 ───┤
  Cause 4 ──┘              │         │              └── Outcome 4
                           │         │
   Prevention Barriers     │         │     Mitigation Barriers
```

## 10. ETA Worksheet Template

### 7.1 Analysis Header

| Field | Value |
|-------|-------|
| Project | [Tên dự án] |
| System | [Hệ thống phân tích] |
| Initiating Event | [Sự kiện khởi phát] |
| IE Frequency/Probability | [P hoặc frequency] |
| Analyst | [Người phân tích] |
| Date | [Ngày] |

### 7.2 Barrier Definition

| # | Barrier | Description | P(Success) | P(Failure) | Source |
|---|---------|-------------|------------|------------|--------|
| B1 | [Tên barrier] | [Mô tả] | [0-1] | [0-1] | [Data source] |

### 7.3 Outcome Summary

| Outcome # | Path | Severity | Probability | Risk Level | Action Required |
|-----------|------|----------|-------------|------------|-----------------|
| O1 | B1✅ → B2✅ | [Level] | [P] | [Low/High] | [Action] |

## 11. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Trực quan theo chiều thời gian (chronological)
- ✅ Xác định được tất cả kịch bản có thể
- ✅ Tính được xác suất từng outcome
- ✅ Đánh giá được hiệu quả của từng safety barrier
- ✅ Kết hợp tốt với FTA (Bow-tie)

### Hạn chế
- ❌ Chỉ xử lý một Initiating Event mỗi lần
- ❌ Binary branching đơn giản hóa quá mức (partial success?)
- ❌ Số lượng outcomes tăng theo hàm mũ (2^n)
- ❌ Giả định barriers độc lập (có thể không đúng)
- ❌ Khó xử lý thứ tự barrier thay đổi theo kịch bản

## 12. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| IEC 62502:2010 | Event tree analysis (ETA) |
| ISO 31010:2019 | Risk assessment techniques |
| NUREG/CR-2300 | PRA Procedures Guide (nuclear) |
| IEC 61508 | Functional safety |

## 13. Tài liệu tham khảo

1. IEC 62502:2010 - Analysis techniques for dependability — Event tree analysis (ETA)
2. ISO 31010:2019 - Risk assessment techniques
3. Ericson, C.A. (2005) - "Hazard Analysis Techniques for System Safety"
4. Andrews, J.D. & Moss, T.R. (2002) - "Reliability and Risk Assessment"
5. NUREG/CR-2300 (1983) - "PRA Procedures Guide"
