# DRBFM (Design Review Based on Failure Mode)

## 1. Tổng quan (Overview)

**DRBFM** (Design Review Based on Failure Mode) là phương pháp phân tích rủi ro tập trung vào **các thay đổi** (changes), được phát triển bởi **Dr. Tatsuhiko Yoshimura** (Toyota) vào cuối thập niên 1990. DRBFM dựa trên nguyên lý:

> **"Problems arise from changes"** — Vấn đề phát sinh từ thay đổi

Thay vì phân tích toàn bộ thiết kế, DRBFM tập trung vào:
- **Intentional changes** (thay đổi có chủ đích): Feature mới, redesign
- **Incidental changes** (thay đổi không chủ đích): Side effects, môi trường thay đổi

### DRBFM vs FMEA

| Aspect | FMEA | DRBFM |
|--------|------|-------|
| Scope | Toàn bộ thiết kế | Chỉ phần thay đổi |
| Focus | Failure modes | Changes & concerns |
| Approach | Bottom-up analysis | Change-focused review |
| Philosophy | Analyze all failures | Analyze change impact |
| Effort | High (comprehensive) | Focused (efficient) |
| Best for | New designs | Incremental changes |
| Origin | US Military (1949) | Toyota (late 1990s) |

## 2. Triết lý GD³ (Good Design, Good Discussion, Good Dissection)

DRBFM được xây dựng trên triết lý **GD³** của Toyota:

### Good Design (Thiết kế tốt)
- Tái sử dụng thiết kế đã được chứng minh (proven designs)
- Chỉ thay đổi khi thực sự cần thiết
- Hiểu rõ lý do thay đổi

### Good Discussion (Thảo luận tốt)
- Cross-functional team review
- Open discussion về concerns
- Không bỏ qua bất kỳ concern nào
- "Worry about changes" — lo lắng có chủ đích

### Good Dissection (Phân tích tốt)
- Phân tích sâu ảnh hưởng của thay đổi
- Xem xét cả direct và indirect effects
- Test và verify kỹ phần thay đổi

## 3. Cấu trúc DRBFM

### 3.1 Các thành phần chính

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CHANGE     │───►│   CONCERN    │───►│  COUNTERMEASURE│
│              │    │              │    │               │
│ What changed?│    │ What could   │    │ What to do    │
│ Why changed? │    │ go wrong?    │    │ about it?     │
└──────────────┘    └──────────────┘    └───────────────┘
```

### 3.2 DRBFM Worksheet Columns

| Column Group | Column | Mô tả |
|-------------|--------|-------|
| **Item** | Component / Function | Phần nào được review |
| **Change** | Change Point | Điểm thay đổi cụ thể |
| | Change Reason | Lý do thay đổi |
| | Previous Design | Thiết kế cũ |
| | New Design | Thiết kế mới |
| **Concern** | Concern about Change | Lo ngại về thay đổi |
| | Possible Effects | Ảnh hưởng có thể |
| | Root Cause of Concern | Nguyên nhân gốc rễ |
| **Evaluation** | Severity | Mức nghiêm trọng |
| | Occurrence | Khả năng xảy ra |
| | Detection | Khả năng phát hiện |
| **Countermeasure** | Design Countermeasure | Biện pháp thiết kế |
| | Validation/Test | Kế hoạch kiểm chứng |
| **Follow-up** | Owner | Người chịu trách nhiệm |
| | Status | Trạng thái |

## 4. Quy trình thực hiện DRBFM

### Phase 1: Identify Changes (Nhận diện thay đổi)

#### 4.1 Liệt kê tất cả thay đổi
- **Intentional changes**: Thay đổi có chủ đích
  - New features
  - Bug fixes
  - Performance optimization
  - Architecture refactoring
  - Library/framework upgrades
  
- **Incidental changes**: Thay đổi không chủ đích (side effects)
  - Dependency updates kéo theo API changes
  - Environment changes (OS, runtime version)
  - Usage pattern changes (load, data volume)
  - Interaction with other changed components

#### 4.2 So sánh Previous vs New Design
- Cho mỗi change point, document:
  - Thiết kế cũ hoạt động như thế nào
  - Thiết kế mới khác gì
  - Phần nào giữ nguyên, phần nào thay đổi

### Phase 2: Identify Concerns (Nhận diện lo ngại)

#### 4.3 "Worry about changes"
Với mỗi change point, hỏi:
- **Chuyện gì có thể sai?** (What could go wrong?)
- **Ảnh hưởng đến chức năng nào?** (What functions are affected?)
- **Ảnh hưởng đến component nào khác?** (What other components?)
- **Điều kiện nào làm concern trở thành thực tế?** (Under what conditions?)
- **Người dùng bị ảnh hưởng thế nào?** (How are users affected?)

#### 4.4 Phân loại Concerns

| Loại | Mô tả | Ví dụ |
|------|--------|-------|
| Functional | Chức năng bị ảnh hưởng | Feature không hoạt động đúng |
| Performance | Hiệu năng bị ảnh hưởng | Response time tăng |
| Compatibility | Tương thích bị ảnh hưởng | API contract break |
| Security | Bảo mật bị ảnh hưởng | New attack surface |
| Data | Dữ liệu bị ảnh hưởng | Migration issues, data loss |
| Usability | Trải nghiệm người dùng | Workflow thay đổi, confusion |

### Phase 3: Evaluate & Countermeasure (Đánh giá & Biện pháp)

#### 4.5 Đánh giá Severity / Occurrence / Detection
- Sử dụng thang đo tương tự FMEA (1-10)
- Tập trung vào concerns có severity cao

#### 4.6 Xác định Countermeasures
- **Design countermeasure**: Thay đổi thiết kế để loại bỏ concern
- **Process countermeasure**: Thêm bước kiểm tra, review
- **Test countermeasure**: Test case cụ thể cho concern

### Phase 4: Review & Follow-up

#### 4.7 DRBFM Review Meeting
- Cross-functional team review
- Thảo luận mở về tất cả concerns
- Không dismiss concern nào mà chưa phân tích kỹ
- Agreement trên countermeasures

#### 4.8 Follow-up
- Track implementation of countermeasures
- Verify effectiveness
- Update DRBFM document

## 5. DRBFM Worksheet Template

| ID | Component | Change Point | Previous Design | New Design | Change Reason | Concern | Possible Effect | Root Cause | S | O | D | Design Countermeasure | Validation Plan | Owner | Status |
|----|-----------|-------------|----------------|------------|---------------|---------|----------------|------------|---|---|---|---------------------|----------------|-------|--------|
| D-001 | [Module] | [Thay đổi] | [Cũ] | [Mới] | [Lý do] | [Lo ngại] | [Ảnh hưởng] | [Nguyên nhân] | [1-10] | [1-10] | [1-10] | [Biện pháp] | [Kế hoạch test] | [Owner] | [Status] |

## 6. Ví dụ: DRBFM cho Software Change

### Context: Upgrade Database từ PostgreSQL 14 → PostgreSQL 16

| ID | Change Point | Previous | New | Concern | Effect | S | O | D | Countermeasure | Validation |
|----|-------------|----------|-----|---------|--------|---|---|---|---------------|------------|
| D-001 | Query optimizer thay đổi | PG14 planner | PG16 planner | Query plan thay đổi → performance regression | Critical queries chậm hơn | 7 | 4 | 3 | Benchmark critical queries trước/sau upgrade | Load test với production-like data |
| D-002 | Default settings thay đổi | PG14 defaults | PG16 defaults | Config không tương thích | Connection issues, memory problems | 6 | 5 | 4 | Review release notes, diff config files | Deploy staging trước production |
| D-003 | Deprecated features removed | Sử dụng deprecated functions | Functions bị remove | Application code sử dụng removed functions | Runtime errors | 9 | 3 | 2 | Scan codebase cho deprecated functions | Full regression test suite |
| D-004 | Extension compatibility | Extensions hoạt động với PG14 | Extensions chưa test PG16 | Extensions không compatible | Feature breakage | 8 | 3 | 5 | Verify compatibility matrix cho mỗi extension | Test mỗi extension individually |
| D-005 | Replication protocol changes | PG14 streaming replication | PG16 replication | Replication break | Data sync failure, split brain | 9 | 2 | 6 | Test replication setup, failover test | DR drill với PG16 |

### Context: Refactor Authentication Module (từ Session-based → JWT)

| ID | Change Point | Previous | New | Concern | Effect | S | O | D | Countermeasure | Validation |
|----|-------------|----------|-----|---------|--------|---|---|---|---------------|------------|
| D-006 | Auth mechanism | Server-side sessions | JWT tokens | Token theft → persistent unauthorized access | Security breach | 9 | 4 | 5 | Short expiry + refresh token + token revocation list | Penetration testing |
| D-007 | Session invalidation | Server can destroy session | JWT valid until expiry | Không thể invalidate ngay khi detect compromise | Extended exposure time | 8 | 3 | 6 | Implement token blacklist in Redis | Test logout + token blacklist |
| D-008 | Token size | Small session ID | JWT payload lớn hơn | Mỗi request gửi token lớn | Bandwidth increase, slower mobile | 4 | 7 | 2 | Minimize JWT claims, use compression | Performance benchmark |
| D-009 | State management | Stateful (server stores session) | Stateless (token contains claims) | Claims stale khi user info thay đổi | User thấy stale data/permissions | 6 | 5 | 4 | Short token expiry (15min) + refresh mechanism | Test permission change propagation |
| D-010 | Secret key management | Session secret | JWT signing key | Key leak → forge bất kỳ token nào | Complete auth bypass | 10 | 2 | 7 | Use asymmetric keys (RS256), key rotation, HSM | Key rotation test, audit logging |

## 7. Phân tích DRBFM dự án CleanBox (Project Analysis)

### 7.1 Context: Planned Changes cho CleanBox v1.1.0 → v1.2.0

Dựa trên kết quả phân tích từ Risk Matrix, SW-FMEA, FTA, ETA, Bow-tie, HAZOP, và STPA, các thay đổi sau được kế hoạch cho CleanBox:

### 7.2 DRBFM Worksheet — Change 1: Thêm Cleanup Confirmation Dialog

| Field | Detail |
|-------|--------|
| **Component** | CleanupService + CleanupView + TrayIcon |
| **Change Point** | Thêm QMessageBox confirmation trước mỗi cleanup action |
| **Previous Design** | Cleanup chạy ngay khi user click "Cleanup Now" (tray hoặc UI) |
| **New Design** | QMessageBox.warning hiển thị preview (N files, X MB) → user Confirm/Cancel |
| **Change Reason** | FTA: No confirmation = Single Point of Failure (P=0.80); STPA: UCA-2 |

| ID | Concern | Possible Effect | Root Cause | S | O | D | Design Countermeasure | Validation Plan |
|----|---------|----------------|------------|---|---|---|---------------------|----------------|
| D-CB-001 | Dialog hiển thị sai file count | User confirm dựa trên info sai | Pre-scan count logic bug | 6 | 3 | 3 | Unit test cho count logic; show "~approximate" | Test với 0, 1, 100, 10000 files |
| D-CB-002 | Dialog block main thread | UI freeze khi scan preview | Preview scan chạy trên main thread | 5 | 4 | 2 | Scan trên worker thread → emit result → show dialog | Test: dialog appears < 2s cho dir 10K files |
| D-CB-003 | Tray cleanup không show dialog | pystray callback không chạy trên Qt thread → QMessageBox crash | Thread affinity issue | 8 | 5 | 4 | Emit signal từ tray → main thread show dialog | Test: tray cleanup → dialog appears (no crash) |
| D-CB-004 | User chọn "Don't ask again" | Bypass toàn bộ confirmation | Có checkbox "remember" | 9 | 2 | 2 | KHÔNG thêm "Don't ask again" checkbox | Code review: verify no bypass option |
| D-CB-005 | Dialog hiện lên khi PC bị lock | Nobody to confirm → cleanup blocked vĩnh viễn | Auto-scheduled cleanup + screen locked | 4 | 3 | 5 | Timeout dialog sau 5 phút → cancel tự động | Test: dialog timeout → cleanup cancelled |

### 7.3 DRBFM Worksheet — Change 2: System Folder Whitelist

| Field | Detail |
|-------|--------|
| **Component** | constants.py + CleanupView + CleanupService |
| **Change Point** | Thêm PROTECTED_PATHS constant, validate khi add directory và khi cleanup |
| **Previous Design** | User có thể thêm bất kỳ directory nào vào cleanup list |
| **New Design** | PROTECTED_PATHS = [WINDIR, PROGRAMFILES, SYSTEM32, APPDATA, ...]; reject add + reject cleanup |
| **Change Reason** | Risk Matrix R-001 (Critical); FMEA FM-CB-001 (RPN=240); STPA REQ-1,7 |

| ID | Concern | Possible Effect | Root Cause | S | O | D | Design Countermeasure | Validation Plan |
|----|---------|----------------|------------|---|---|---|---------------------|----------------|
| D-CB-006 | Whitelist không đủ paths | System folder khác vẫn bị xóa | Chỉ list vài paths cơ bản | 9 | 3 | 4 | Comprehensive list + "starts with" check thay vì exact match | Test: 20+ system paths → all blocked |
| D-CB-007 | Case sensitivity mismatch | C:\WINDOWS vs C:\Windows → bypass whitelist | Windows paths case-insensitive nhưng Python so sánh case-sensitive | 9 | 4 | 3 | os.path.normcase() + lower() cho tất cả comparisons | Test: various cases → all blocked |
| D-CB-008 | Symlink/junction bypass | Symlink trỏ đến system folder → bypass whitelist | os.path.realpath không resolve junctions | 8 | 2 | 5 | os.path.realpath() + re-check after resolve | Test: create symlink to WINDIR → blocked |
| D-CB-009 | Whitelist quá aggressive | Block folders user thực sự muốn clean | Sub-folder of protected path bị block sai | 5 | 3 | 2 | Chỉ block level 1 protected paths, cho phép sub-dirs | Test: C:\Users\X\Downloads → allowed |
| D-CB-010 | Config migration | Existing config có protected paths → lỗi khi load | Old config không có validation | 6 | 3 | 3 | Migrate: filter out protected paths on load + notify user | Test: old config with C:\Windows → filtered + notified |

### 7.4 DRBFM Worksheet — Change 3: Atomic Config Write

| Field | Detail |
|-------|--------|
| **Component** | ConfigManager (`shared/config/manager.py`) |
| **Change Point** | Thay đổi file write thành atomic: write .tmp → os.replace() + .bak backup |
| **Previous Design** | Direct open(config, 'w') → json.dump() |
| **New Design** | Write config.json.tmp → os.replace(tmp, config) + copy config → config.bak |
| **Change Reason** | FMEA FM-CB-008 (RPN=112); FTA MCS-4; STPA REQ-4 |

| ID | Concern | Possible Effect | Root Cause | S | O | D | Design Countermeasure | Validation Plan |
|----|---------|----------------|------------|---|---|---|---------------------|----------------|
| D-CB-011 | os.replace() fail cross-drive | Nếu tmp và config trên drives khác → fail | %TEMP% vs %APPDATA% trên drives khác | 7 | 2 | 4 | Tạo .tmp trong cùng directory với config | Test: verify .tmp same dir as config |
| D-CB-012 | Backup file cũng corrupt | Backup bị overwrite bởi corrupt version | Backup trước replace → backup = corrupt | 8 | 2 | 4 | Backup TRƯỚC write (copy current → .bak) | Test: backup → write fail → .bak valid |
| D-CB-013 | Permission denied cho .tmp | Config dir read-only hoặc protected | Antivirus lock hoặc admin policies | 5 | 2 | 3 | Catch PermissionError → fallback direct write + warn | Test: read-only dir → graceful fallback |
| D-CB-014 | .tmp file left behind | Crash sau write .tmp, trước replace | Power loss giữa 2 operations | 3 | 2 | 4 | Cleanup stale .tmp files on startup | Test: stale .tmp exists → cleaned up |

### 7.5 DRBFM Worksheet — Change 4: Memory Management cho StorageMonitor

| Field | Detail |
|-------|--------|
| **Component** | StorageMonitor (`features/storage_monitor/service.py`) |
| **Change Point** | Thêm explicit object cleanup + periodic gc.collect() |
| **Previous Design** | psutil objects tạo mỗi polling cycle, rely on Python GC |
| **New Design** | Explicit del DriveInfo objects + gc.collect() mỗi 100 cycles |
| **Change Reason** | Risk Matrix R-002; FMEA FM-CB-005 (RPN=105); HAZOP MORE/Quantity |

| ID | Concern | Possible Effect | Root Cause | S | O | D | Design Countermeasure | Validation Plan |
|----|---------|----------------|------------|---|---|---|---------------------|----------------|
| D-CB-015 | gc.collect() gây freeze | GC pause tạo UI stutter | GC chạy trên polling thread → block | 3 | 4 | 2 | gc.collect() chỉ chạy trên background thread, không main | Test: GC during poll → no UI impact |
| D-CB-016 | Del object quá sớm | Access deleted object → crash | Signal reference object đã del | 7 | 2 | 3 | Copy data trước del; emit signal với copied data | Test: emit signal → del object → no crash |
| D-CB-017 | Memory không thực sự giảm | Python không release memory cho OS | CPython memory allocator behavior | 3 | 5 | 5 | Monitor RSS via psutil self-check; restart timer nếu > 100MB | Test: long-run RSS stays < 100MB |

### 7.6 DRBFM Summary

| Change | # Concerns | Critical (S≥8) | Action Required |
|--------|-----------|----------------|----------------|
| 1: Confirmation Dialog | 5 | 1 (D-CB-003: thread affinity) | Fix tray callback thread safety |
| 2: System Folder Whitelist | 5 | 3 (D-CB-006, 007, 008) | Comprehensive + case-insensitive + symlink |
| 3: Atomic Config Write | 4 | 1 (D-CB-012: backup timing) | Backup before write, not after |
| 4: Memory Management | 3 | 1 (D-CB-016: premature del) | Copy before delete pattern |
| **Total** | **17** | **6** | |

## 8. Kế hoạch triển khai và xác minh DRBFM (Implementation & Verification Plan)

### 8.1 Implementation Checklist per Change

#### Change 1: Confirmation Dialog
- [ ] Implement preview scan worker (QThread)
- [ ] Create confirmation QMessageBox with file count + size
- [ ] Wire tray callback → signal → main thread dialog
- [ ] Add dialog timeout (5 min → auto-cancel)
- [ ] **Test**: D-CB-001 to D-CB-005 unit + integration tests

#### Change 2: System Folder Whitelist
- [ ] Define PROTECTED_PATHS in constants.py (20+ paths)
- [ ] Add normcase() + lower() path normalization
- [ ] Add os.path.realpath() symlink resolution
- [ ] Add validation in CleanupView.add_directory()
- [ ] Add validation in CleanupService.cleanup_directory()
- [ ] Add config migration logic for existing configs
- [ ] **Test**: D-CB-006 to D-CB-010 unit tests (30+ test cases)

#### Change 3: Atomic Config Write
- [ ] Implement write-to-tmp in same directory
- [ ] Implement backup (copy → .bak) BEFORE write
- [ ] Implement os.replace() atomic swap
- [ ] Add stale .tmp cleanup on startup
- [ ] Add PermissionError fallback
- [ ] **Test**: D-CB-011 to D-CB-014 unit + crash simulation

#### Change 4: Memory Management
- [ ] Add explicit del for DriveInfo objects after signal emit
- [ ] Add gc.collect() every 100 polling cycles
- [ ] Add self-monitoring RSS check
- [ ] Copy signal data before del
- [ ] **Test**: D-CB-015 to D-CB-017 integration + long-run tests

### 8.2 DRBFM Review Meeting Plan

| Meeting | Scope | Participants | Duration |
|---------|-------|-------------|----------|
| Review 1 | Changes 1 + 2 (UI safety) | Dev Lead, Frontend Dev, QA | 60 min |
| Review 2 | Changes 3 + 4 (Backend reliability) | Dev Lead, Backend Dev, QA | 45 min |
| Final Review | All changes integrated | Full team | 30 min |

### 8.3 Verification Matrix

| Concern ID | Unit Test | Integration Test | Manual Test | Code Review |
|-----------|-----------|-----------------|-------------|-------------|
| D-CB-001 | ✅ Count accuracy | — | — | ✅ |
| D-CB-002 | — | ✅ Dialog latency < 2s | — | ✅ |
| D-CB-003 | — | ✅ Tray → Qt thread | ✅ Visual | ✅ |
| D-CB-004 | — | — | ✅ No bypass option | ✅ |
| D-CB-005 | ✅ Timeout logic | — | ✅ Screen lock test | — |
| D-CB-006 | ✅ 20+ paths | — | — | ✅ |
| D-CB-007 | ✅ Case variants | — | — | ✅ |
| D-CB-008 | ✅ Symlink creation | — | — | ✅ |
| D-CB-009 | ✅ Sub-dir allowed | — | — | ✅ |
| D-CB-010 | ✅ Migration logic | ✅ Old config load | — | ✅ |
| D-CB-011 | ✅ Same dir check | — | — | — |
| D-CB-012 | ✅ Backup timing | ✅ Crash simulation | — | ✅ |
| D-CB-013 | ✅ Permission fallback | — | ✅ Read-only dir | — |
| D-CB-014 | ✅ Stale cleanup | — | — | — |
| D-CB-015 | — | ✅ GC no UI freeze | — | ✅ |
| D-CB-016 | ✅ Copy before del | — | — | ✅ |
| D-CB-017 | — | ✅ Long-run RSS | — | — |

### 8.4 Acceptance Criteria

| Criteria | Metric | Target |
|----------|--------|--------|
| All concerns addressed | Concerns with countermeasure | 17/17 (100%) |
| Critical concerns resolved | S ≥ 8 concerns verified | 6/6 (100%) |
| Test coverage | Concerns with ≥ 1 automated test | ≥ 15/17 (88%) |
| DRBFM review completed | Review meetings held | 3/3 |
| No regression | Existing test suite passes | 100% pass |
| Post-implementation RPN | All concerns re-scored | No item S×O×D > 80 |

## 9. DRBFM trong Software Development Lifecycle

### Khi nào áp dụng DRBFM?

| Trigger | Mô tả | DRBFM Focus |
|---------|-------|-------------|
| Feature Addition | Thêm tính năng mới | Impact lên existing features |
| Bug Fix | Sửa lỗi | Side effects của fix |
| Refactoring | Cải thiện code structure | Behavioral changes |
| Dependency Update | Upgrade libraries/frameworks | Breaking changes, deprecations |
| Infrastructure Change | Change DB, cloud, runtime | Compatibility, performance |
| Architecture Change | Monolith → microservices | Communication, data consistency |
| Migration | Platform/technology migration | Data integrity, feature parity |

### Integration với Development Process

```
Requirement → Design → DRBFM Review → Implementation → Testing (guided by DRBFM) → Release
                 │                                          │
                 └──── Change Points ────────────────────────┘
                        identified here                verified here
```

## 10. DRBFM Review Meeting Guidelines

### Participants

| Role | Responsibility |
|------|---------------|
| Change Owner | Present changes, explain rationale |
| Reviewer(s) | Challenge, raise concerns |
| Domain Expert | Assess technical impact |
| QA Engineer | Define validation approach |
| Facilitator | Guide discussion, ensure coverage |

### Meeting Structure

1. **Presentation** (15 min): Change owner presents all change points
2. **Concern Discussion** (30-45 min): Team raises concerns for each change
3. **Countermeasure Agreement** (15-20 min): Agree on countermeasures
4. **Action Items** (10 min): Assign owners and deadlines

### Discussion Rules
- ✅ "What if..." questions are encouraged
- ✅ No concern is too small to discuss
- ✅ Focus on change impact, not general quality
- ❌ Don't dismiss concerns without analysis
- ❌ Don't turn into a general design review

## 11. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Hiệu quả cao: tập trung vào changes, không phân tích lại toàn bộ
- ✅ Phù hợp với agile/iterative development
- ✅ Phát hiện side effects của changes
- ✅ Khuyến khích "worry culture" — lo lắng có chủ đích
- ✅ Cross-functional discussion tạo shared understanding
- ✅ Traceability: Change → Concern → Countermeasure → Test

### Hạn chế
- ❌ Không phù hợp cho thiết kế hoàn toàn mới (dùng FMEA)
- ❌ Phụ thuộc vào khả năng nhận diện changes
- ❌ Yêu cầu kiến thức sâu về previous design
- ❌ Có thể bỏ sót incidental changes
- ❌ Cần văn hóa cởi mở, không đổ lỗi

## 12. So sánh DRBFM với các phương pháp khác

| Criteria | Risk Matrix | FMEA | FTA | HAZOP | STPA | DRBFM |
|----------|------------|------|-----|-------|------|-------|
| Focus | General risk | All failure modes | One top event | Deviations | Unsafe control | Changes |
| Effort | Low | High | Medium | High | Medium-High | Low-Medium |
| Best for | Quick assessment | Comprehensive analysis | Root cause analysis | Complex processes | System interactions | Incremental changes |
| Agile-friendly | Yes | No (heavy) | Moderate | No (workshop) | Moderate | Yes |

## 13. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| Toyota DRBFM Guidelines | Original Toyota methodology |
| SAE J2886 | DRBFM standard for automotive |
| AIAG & VDA FMEA Handbook | References DRBFM as complementary method |
| ISO 26262 | Functional safety — DRBFM for change management |

## 14. Tài liệu tham khảo

1. Yoshimura, T. (2010) - "DRBFM: Design Review Based on Failure Mode" (Original paper)
2. Schorn, M. (2005) - "DRBFM — A Method for Systematic Change Management"
3. SAE J2886 - "Design Review Based on Failure Mode (DRBFM)"
4. Schmitt, C. (2014) - "DRBFM: The Toyota Way of Change Management"
5. AIAG & VDA FMEA Handbook (2019) - Supplementary DRBFM guidance
