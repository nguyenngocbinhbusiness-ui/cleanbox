# Bow-Tie Analysis

## 1. Tổng quan (Overview)

**Bow-Tie Analysis** (Phân tích Nơ thắt) là phương pháp đánh giá rủi ro trực quan, kết hợp **FTA** (Fault Tree Analysis) và **ETA** (Event Tree Analysis) vào một sơ đồ duy nhất hình nơ thắt (bow-tie). Phương pháp này cung cấp cái nhìn toàn cảnh về:

- **Threats** (Mối đe dọa) → nguyên nhân dẫn đến hazard event
- **Hazard Event** (Sự kiện nguy hại) → tâm điểm của sơ đồ
- **Consequences** (Hậu quả) → kết quả nếu hazard event xảy ra
- **Prevention Barriers** (Rào cản phòng ngừa) → ngăn threats gây ra hazard
- **Mitigation Barriers** (Rào cản giảm thiểu) → giảm severity của consequences

## 2. Cấu trúc Bow-Tie Diagram

```
   THREATS              PREVENTION          HAZARD          MITIGATION         CONSEQUENCES
   (Causes)             BARRIERS            EVENT           BARRIERS           (Effects)
                                              │
  ┌─────────┐     ┌───┐  ┌───┐              │              ┌───┐  ┌───┐     ┌────────────┐
  │ Threat 1├─────┤PB1├──┤PB2├──────┐       │       ┌──────┤MB1├──┤MB2├─────┤Consequence1│
  └─────────┘     └───┘  └───┘      │       │       │      └───┘  └───┘     └────────────┘
                                     │       │       │
  ┌─────────┐     ┌───┐             │  ┌────┴────┐  │      ┌───┐            ┌────────────┐
  │ Threat 2├─────┤PB3├─────────────┼──┤ HAZARD  ├──┼──────┤MB3├────────────┤Consequence2│
  └─────────┘     └───┘             │  │  EVENT  │  │      └───┘            └────────────┘
                                     │  └────┬────┘  │
  ┌─────────┐     ┌───┐  ┌───┐      │       │       │      ┌───┐  ┌───┐    ┌────────────┐
  │ Threat 3├─────┤PB4├──┤PB5├──────┘       │       └──────┤MB4├──┤MB5├────┤Consequence3│
  └─────────┘     └───┘  └───┘              │              └───┘  └───┘    └────────────┘
                                              │
        ◄──── FTA Side ────►                  │            ◄──── ETA Side ────►
                                              │
                              ┌────────────────┴────────────────┐
                              │    Escalation Factor Controls   │
                              └─────────────────────────────────┘
```

## 3. Các thành phần chi tiết

### 3.1 Threats (Mối đe dọa)

Các nguyên nhân có thể dẫn đến Hazard Event.

| Loại Threat | Ví dụ phần mềm |
|------------|-----------------|
| Human Error | Developer commit code lỗi, sai cấu hình |
| Technical Failure | Hardware crash, network outage |
| External Event | DDoS attack, third-party API down |
| Process Failure | Missing code review, skipped testing |
| Environmental | Power outage, data center incident |

### 3.2 Prevention Barriers (Rào cản phòng ngừa)

Ngăn threats dẫn đến hazard event.

| Barrier | Mô tả | Loại |
|---------|-------|------|
| Code Review | Peer review trước khi merge | Procedural |
| Automated Testing | Unit/Integration/E2E tests | Technical |
| Static Analysis | SonarQube, linting tools | Technical |
| Input Validation | Validate tất cả input | Technical |
| Access Control | RBAC, least privilege | Technical |
| CI/CD Pipeline | Automated build & deploy checks | Technical |
| Training | Security awareness training | Procedural |

### 3.3 Hazard Event (Sự kiện nguy hại)

Sự kiện trung tâm — điểm mà mọi threat hướng đến và mọi consequence bắt nguồn từ.

Ví dụ: "Production data breach", "System complete outage", "Data corruption in production"

### 3.4 Mitigation Barriers (Rào cản giảm thiểu)

Giảm severity sau khi hazard event đã xảy ra.

| Barrier | Mô tả | Loại |
|---------|-------|------|
| Monitoring & Alerting | Real-time monitoring, PagerDuty | Technical |
| Auto Failover | Database replica, load balancer | Technical |
| Backup & Recovery | Automated backup, DR plan | Technical |
| Incident Response Plan | Runbook, on-call rotation | Procedural |
| Rollback Mechanism | Feature flags, blue-green deploy | Technical |
| Communication Plan | Status page, customer notification | Procedural |

### 3.5 Escalation Factors

Các yếu tố làm **suy yếu** barriers:

| Escalation Factor | Ảnh hưởng |
|-------------------|----------|
| Barrier không được maintain | Test suite outdated, false positives |
| Thiếu nhân lực | Code review bị skip |
| Time pressure | Testing bị rút ngắn |
| Thiếu training | Sai quy trình |
| Technical debt | Barriers bị bypass |

## 4. Quy trình xây dựng Bow-Tie

### Bước 1: Xác định Hazard Event
- Chọn hazard event cụ thể, rõ ràng
- Một Bow-Tie diagram cho một hazard event
- Ví dụ: "Unauthorized access to customer data"

### Bước 2: Xác định Threats (bên trái)
- Brainstorming các nguyên nhân có thể
- Phân loại theo loại (human, technical, external...)
- Sử dụng kết quả từ FTA, FMEA nếu có

### Bước 3: Xác định Prevention Barriers
- Với mỗi threat, liệt kê barriers ngăn chặn
- Đánh giá hiệu quả của từng barrier
- Xác định gaps (threats không có barrier)

### Bước 4: Xác định Consequences (bên phải)
- Liệt kê tất cả hậu quả có thể
- Phân loại theo severity
- Sử dụng kết quả từ ETA nếu có

### Bước 5: Xác định Mitigation Barriers
- Với mỗi consequence, liệt kê barriers giảm thiểu
- Đánh giá hiệu quả của từng barrier
- Xác định gaps

### Bước 6: Xác định Escalation Factors
- Yếu tố nào làm barrier kém hiệu quả?
- Biện pháp kiểm soát escalation factors?

### Bước 7: Đánh giá và hành động
- Barrier nào yếu nhất? → Cần tăng cường
- Threat nào không có barrier? → Cần thêm barrier
- Consequence nào nghiêm trọng nhất? → Ưu tiên mitigation

## 5. Ví dụ: Bow-Tie cho "Production Data Breach"

### Hazard Event: Customer Data Breach in Production

#### Threats & Prevention Barriers

| # | Threat | Prevention Barriers | Barrier Status |
|---|--------|-------------------|----------------|
| T1 | SQL Injection Attack | PB1: WAF, PB2: Input Validation, PB3: Parameterized Queries | ✅ Strong |
| T2 | Stolen Credentials | PB4: MFA, PB5: Password Policy, PB6: Session Management | ✅ Strong |
| T3 | Insider Threat | PB7: Access Control (RBAC), PB8: Audit Logging, PB9: Data Encryption | ⚠️ Moderate |
| T4 | Vulnerable Dependency | PB10: Dependency Scanning (Dependabot), PB11: Regular Updates | ⚠️ Moderate |
| T5 | Misconfiguration | PB12: Infrastructure as Code, PB13: Config Review | ❌ Weak |

#### Consequences & Mitigation Barriers

| # | Consequence | Mitigation Barriers | Barrier Status |
|---|------------|---------------------|----------------|
| C1 | Customer PII Exposed | MB1: Data Encryption at Rest, MB2: Data Masking | ✅ Strong |
| C2 | Financial Loss | MB3: Cyber Insurance, MB4: Incident Response Plan | ⚠️ Moderate |
| C3 | Regulatory Penalty | MB5: Compliance Documentation, MB6: Legal Response Team | ⚠️ Moderate |
| C4 | Reputation Damage | MB7: Communication Plan, MB8: Customer Support Escalation | ❌ Weak |

#### Gap Analysis

| Gap | Description | Priority | Recommended Action |
|-----|------------|----------|-------------------|
| GAP-1 | T5 (Misconfiguration) có barrier yếu | High | Implement automated config validation |
| GAP-2 | C4 (Reputation) thiếu mitigation mạnh | High | Develop crisis communication plan |
| GAP-3 | T3 (Insider) cần thêm monitoring | Medium | Implement DLP và behavior analytics |

## 6. Barrier Assessment

### Barrier Quality Criteria

| Criteria | Mô tả | Score |
|----------|-------|-------|
| Effectiveness | Barrier ngăn chặn/giảm thiểu rủi ro tốt không? | 1-5 |
| Independence | Barrier hoạt động độc lập không? | 1-5 |
| Auditability | Có thể kiểm tra barrier hoạt động không? | 1-5 |
| Reliability | Barrier có đáng tin cậy không? | 1-5 |
| Maintainability | Barrier có dễ bảo trì không? | 1-5 |

### Barrier Health Score

```
Barrier Health = (Effectiveness + Independence + Auditability + Reliability + Maintainability) / 5

Score Interpretation:
  4.0-5.0: Strong (Excellent) ✅
  3.0-3.9: Adequate ⚠️
  2.0-2.9: Weak — needs improvement ❌
  1.0-1.9: Critical — immediate action required 🔴
```

## 7. Bow-Tie Report Template

### 7.1 Summary

| Field | Value |
|-------|-------|
| Hazard Event | [Sự kiện nguy hại] |
| Number of Threats | [Số lượng] |
| Number of Consequences | [Số lượng] |
| Prevention Barriers | [Số lượng] (Strong: X, Moderate: Y, Weak: Z) |
| Mitigation Barriers | [Số lượng] (Strong: X, Moderate: Y, Weak: Z) |
| Critical Gaps | [Số lượng] |

### 7.2 Action Items

| # | Gap/Issue | Action | Priority | Owner | Target Date | Status |
|---|----------|--------|----------|-------|-------------|--------|
| 1 | [Mô tả] | [Hành động] | [H/M/L] | [Owner] | [Date] | [Status] |

## 7. Phân tích Bow-Tie dự án CleanBox (Project Analysis)

### 7.1 Hazard Event: "Mất dữ liệu người dùng do CleanBox Cleanup"

```
   THREATS              PREVENTION          HAZARD          MITIGATION         CONSEQUENCES
                        BARRIERS            EVENT           BARRIERS
                                              │
  ┌──────────┐    ┌────┐  ┌────┐             │             ┌────┐  ┌────┐    ┌──────────────┐
  │T1: User  ├────┤PB1 ├──┤PB2 ├────┐        │      ┌─────┤MB1 ├──┤MB2 ├────┤C1: File loss │
  │adds wrong│    │    │  │    │    │        │      │     │    │  │    │    │(recoverable) │
  │folder    │    └────┘  └────┘    │        │      │     └────┘  └────┘    └──────────────┘
  └──────────┘                      │        │      │
                                    │   ┌────┴───┐  │     ┌────┐             ┌──────────────┐
  ┌──────────┐    ┌────┐            ├───┤ DATA   ├──┼─────┤MB3 ├─────────────┤C2: Config    │
  │T2: Tray  ├────┤PB3 ├───────────┤   │ LOSS   │  │     │    │             │reset to      │
  │quick     │    │    │            │   │ EVENT  │  │     └────┘             │defaults      │
  │cleanup   │    └────┘            │   └────┬───┘  │                        └──────────────┘
  └──────────┘                      │        │      │
                                    │        │      │     ┌────┐  ┌────┐     ┌──────────────┐
  ┌──────────┐    ┌────┐  ┌────┐    │        │      └─────┤MB4 ├──┤MB5 ├─────┤C3: Permanent │
  │T3: Config├────┤PB4 ├──┤PB5 ├────┘        │            │    │  │    │     │data loss     │
  │corrupt   │    │    │  │    │             │            └────┘  └────┘     │(unrecoverable│
  └──────────┘    └────┘  └────┘             │                               └──────────────┘
                                              │
  ┌──────────┐    ┌────┐                     │             ┌────┐            ┌──────────────┐
  │T4: Race  ├────┤PB6 ├────────────────────-┘      ┌─────┤MB6 ├────────────┤C4: App crash │
  │condition │    │    │                             │     │    │            │user frustration
  └──────────┘    └────┘                             │     └────┘            └──────────────┘
```

### 7.2 Threats & Prevention Barriers — Chi tiết

| # | Threat | Prevention Barriers | Status |
|---|--------|-------------------|--------|
| T1 | User thêm thư mục quan trọng vào cleanup list | **PB1**: System folder whitelist (Windows, Program Files, System32, AppData) | ❌ **Chưa có** |
| | | **PB2**: Warning dialog khi thêm folder chứa > 100 files | ❌ **Chưa có** |
| T2 | Tray "Cleanup Now" không có preview | **PB3**: Confirmation dialog + cleanup preview (số files, tổng size) | ❌ **Chưa có** |
| T3 | Config file bị corrupt | **PB4**: Atomic write (temp → rename) cho config.json | ❌ **Chưa có** |
| | | **PB5**: Config backup (.bak) trước mỗi lần write | ❌ **Chưa có** |
| T4 | Race condition cleanup worker + config | **PB6**: Signal/Slot architecture (thread-safe Qt signals) | ✅ **Đã có** |

### 7.3 Consequences & Mitigation Barriers — Chi tiết

| # | Consequence | Mitigation Barriers | Status |
|---|------------|---------------------|--------|
| C1 | Mất files (recoverable từ Recycle Bin) | **MB1**: Di chuyển vào Recycle Bin thay vì xóa vĩnh viễn | ✅ **Đã có** (winshell) |
| | | **MB2**: Cleanup report với danh sách files đã xóa | ⚠️ **Có một phần** (summary only) |
| C2 | Config reset to defaults | **MB3**: Fallback to default config khi file corrupt | ✅ **Đã có** |
| C3 | Mất dữ liệu vĩnh viễn | **MB4**: Undo mechanism (restore từ Recycle Bin) | ❌ **Chưa có** |
| | | **MB5**: Cleanup log file (audit trail) | ❌ **Chưa có** |
| C4 | App crash | **MB6**: Global exception handler + graceful restart | ⚠️ **Có một phần** (logging có, restart chưa) |

### 7.4 Gap Analysis — CleanBox

| Gap | Description | Priority | Current State | Required Action |
|-----|------------|----------|---------------|-----------------|
| **GAP-1** | T1 không có prevention barrier (no whitelist) | 🔴 Critical | Không có protection | Implement PROTECTED_PATHS whitelist |
| **GAP-2** | T2 không có confirmation trước tray cleanup | 🔴 Critical | Direct cleanup | Add confirmation + preview dialog |
| **GAP-3** | T3 config write không atomic | 🟠 High | Direct file.write() | Implement atomic write pattern |
| **GAP-4** | C3 không có undo mechanism | 🟠 High | Không khôi phục được | Add cleanup history + undo |
| **GAP-5** | C1 cleanup report thiếu chi tiết | 🟡 Medium | Summary count only | Detailed file list in report |
| **GAP-6** | C4 app crash không auto-restart | 🟡 Medium | Log only | Add watchdog / restart mechanism |

### 7.5 Barrier Assessment — CleanBox

| Barrier | Effectiveness | Independence | Auditability | Reliability | Maintainability | Health Score |
|---------|-------------|-------------|-------------|-------------|----------------|-------------|
| PB1 (Whitelist) | — | — | — | — | — | ❌ Not implemented |
| PB2 (Warning dialog) | — | — | — | — | — | ❌ Not implemented |
| PB3 (Confirm dialog) | — | — | — | — | — | ❌ Not implemented |
| PB4 (Atomic write) | — | — | — | — | — | ❌ Not implemented |
| PB5 (Config backup) | — | — | — | — | — | ❌ Not implemented |
| PB6 (Signal/Slot) | 5 | 5 | 3 | 5 | 4 | ✅ **4.4** Strong |
| MB1 (Recycle Bin) | 4 | 5 | 4 | 3 | 4 | ✅ **4.0** Strong |
| MB2 (Cleanup report) | 2 | 5 | 2 | 4 | 3 | ⚠️ **3.2** Adequate |
| MB3 (Default fallback) | 4 | 5 | 3 | 5 | 5 | ✅ **4.4** Strong |
| MB6 (Exception handler) | 3 | 4 | 3 | 3 | 3 | ⚠️ **3.2** Adequate |

## 8. Kế hoạch triển khai và xác minh Bow-Tie (Implementation & Verification Plan)

### 8.1 Implementation Roadmap

| Phase | Barriers to Implement | Description | Verification |
|-------|----------------------|-------------|-------------|
| **Phase 1** (v1.1.0) | PB1, PB2, PB3 | Prevention barriers cho T1, T2 | Unit tests + E2E tests |
| **Phase 2** (v1.1.0) | PB4, PB5 | Config protection | Unit tests + crash simulation |
| **Phase 3** (v1.2.0) | MB2 (improve), MB4, MB5 | Mitigation improvements | Integration tests |
| **Phase 4** (v1.2.0) | MB6 (improve) | Crash recovery | Manual + integration tests |

### 8.2 Barrier Implementation Specs

| Barrier | Implementation Detail | Test Strategy |
|---------|---------------------|--------------|
| PB1 (Whitelist) | `PROTECTED_PATHS = [os.environ['WINDIR'], os.environ['PROGRAMFILES'], ...]` in constants.py; check in CleanupView.add_directory() | `test_whitelist_blocks_system_folders()` — 10+ system paths tested |
| PB2 (Warning) | QMessageBox.warning when directory contains > 100 items | `test_warning_shown_for_large_directory()` |
| PB3 (Confirm) | QMessageBox with cleanup preview (N files, X MB) before cleanup starts | `test_confirmation_dialog_before_cleanup()`, `test_cancel_aborts_cleanup()` |
| PB4 (Atomic write) | Write to config.json.tmp → os.replace() → delete .tmp | `test_atomic_write_survives_interrupt()` |
| PB5 (Backup) | Copy config.json → config.json.bak before write | `test_backup_created_before_write()`, `test_restore_from_backup()` |
| MB4 (Undo) | Store cleanup manifest in %APPDATA%/.cleanbox/cleanup_history/ | `test_undo_restores_files_from_recycle_bin()` |
| MB5 (Audit log) | Write cleanup actions to cleanup.log with timestamps | `test_cleanup_log_records_all_deletions()` |

### 8.3 Post-Implementation Barrier Re-Assessment Target

| Barrier | Current Score | Target Score | Gap to Close |
|---------|-------------|-------------|-------------|
| PB1-PB5 | 0 (not impl) | ≥ 4.0 (Strong) | Full implementation |
| MB2 (Report) | 3.2 | ≥ 4.0 | Add detailed file list |
| MB6 (Exception) | 3.2 | ≥ 4.0 | Add auto-restart |
| **Overall System** | **3 of 10 barriers active** | **10 of 10 active** | |

## 9. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Trực quan nhất trong các phương pháp phân tích rủi ro
- ✅ Cái nhìn toàn cảnh: causes → event → consequences
- ✅ Đánh giá được hiệu quả barriers
- ✅ Dễ giao tiếp với stakeholders non-technical
- ✅ Kết hợp FTA + ETA trong một diagram
- ✅ Tập trung vào barriers (actionable)

### Hạn chế
- ❌ Đơn giản hóa quá mức cho hệ thống phức tạp
- ❌ Không phân tích được barrier dependencies
- ❌ Thiếu quantitative analysis (so với FTA/ETA riêng)
- ❌ Một diagram chỉ cho một hazard event
- ❌ Khó thể hiện dynamic/temporal aspects

## 10. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| ISO 31010:2019 | Risk assessment techniques — bao gồm Bow-tie |
| CCPS (2018) | Bow Ties in Risk Management |
| Energy Institute (2018) | Guidance on the bow tie method |
| CGE Risk Management Solutions | BowTieXP methodology |

## 11. Tài liệu tham khảo

1. ISO 31010:2019 - Risk assessment techniques
2. CCPS (2018) - "Bow Ties in Risk Management: A Concept Book for Process Safety"
3. de Ruijter, A. & Guldenmund, F. (2016) - "The bowtie method: A review"
4. Energy Institute (2018) - "Guidance on meeting expectations of EI 15 using bow-ties"
5. Chevreau, F.R. et al. (2006) - "Organizing learning processes on risks by using the bow-tie representation"
