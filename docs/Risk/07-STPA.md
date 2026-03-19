# STPA (System-Theoretic Process Analysis)

## 1. Tổng quan (Overview)

**STPA** (System-Theoretic Process Analysis) là phương pháp phân tích nguy hại **dựa trên lý thuyết hệ thống** (systems theory), được phát triển bởi **Nancy Leveson** (MIT). Thay vì tập trung vào component failures như FMEA/FTA, STPA phân tích **unsafe control actions** và **loss scenarios** trong toàn bộ hệ thống.

### Triết lý cốt lõi (STAMP Model)

**STAMP** (Systems-Theoretic Accident Model and Processes):
- Tai nạn không chỉ do **component failure**, mà do **inadequate control** (kiểm soát không đầy đủ)
- An toàn là **control problem**, không chỉ là **reliability problem**
- Cần phân tích **interactions** giữa các components, không chỉ individual failures
- Con người, phần mềm, tổ chức đều là thành phần của hệ thống kiểm soát

### So sánh với phương pháp truyền thống

| Aspect | Traditional (FMEA/FTA) | STPA |
|--------|----------------------|------|
| Focus | Component failures | Unsafe control actions |
| Assumption | Accidents = chain of failure events | Accidents = inadequate control |
| Software | Khó áp dụng (SW không "fail" theo nghĩa truyền thống) | Thiết kế cho SW-intensive systems |
| Scope | Component-level | System-level (bao gồm human, org) |
| Interactions | Hạn chế | Phân tích sâu interactions |

## 2. STPA Framework — 4 Bước

### Overview

```
  Step 1: Define Purpose of the Analysis
       │
       ▼
  Step 2: Model the Control Structure
       │
       ▼
  Step 3: Identify Unsafe Control Actions (UCAs)
       │
       ▼
  Step 4: Identify Loss Scenarios
```

## 3. Step 1: Define Purpose of the Analysis

### 3.1 Xác định Losses (Tổn thất)

Losses là các kết quả không mong muốn ở mức hệ thống.

| ID | Loss | Mô tả |
|----|------|-------|
| L-1 | Loss of life or injury | Ảnh hưởng sức khỏe/tính mạng |
| L-2 | Loss of data | Mất dữ liệu |
| L-3 | Loss of system availability | Hệ thống không khả dụng |
| L-4 | Loss of privacy | Vi phạm quyền riêng tư |
| L-5 | Financial loss | Thiệt hại tài chính |

### 3.2 Xác định System-level Hazards

Hazards là các trạng thái hệ thống có thể dẫn đến losses.

| ID | Hazard | Related Losses |
|----|--------|---------------|
| H-1 | System provides incorrect data to user | L-2, L-5 |
| H-2 | System allows unauthorized access | L-2, L-4, L-5 |
| H-3 | System becomes unresponsive | L-3, L-5 |
| H-4 | System corrupts stored data | L-2, L-5 |

### 3.3 Xác định System-level Safety Constraints

| ID | Safety Constraint | Related Hazard |
|----|------------------|----------------|
| SC-1 | System must validate all data before presenting to user | H-1 |
| SC-2 | System must authenticate and authorize all access | H-2 |
| SC-3 | System must respond within defined time limits | H-3 |
| SC-4 | System must ensure data integrity during all operations | H-4 |

## 4. Step 2: Model the Control Structure

### 4.1 Control Structure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM BOUNDARY                               │
│                                                                  │
│  ┌──────────────┐         Control Actions        ┌────────────┐ │
│  │              │ ───────────────────────────────►│            │ │
│  │  CONTROLLER  │                                 │ CONTROLLED │ │
│  │              │ ◄───────────────────────────────│  PROCESS   │ │
│  │  (Process    │         Feedback                │            │ │
│  │   Model)     │                                 │  (Actuators│ │
│  │              │                                 │   Sensors) │ │
│  └──────┬───────┘                                 └────────────┘ │
│         │                                                        │
│    ┌────┴────┐                                                   │
│    │ Process │  Controller's internal model                      │
│    │  Model  │  of the controlled process                        │
│    └─────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Ví dụ: Control Structure cho Web Application

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌─────────┐      ┌──────────────┐      ┌───────────────┐        │
│  │  Admin   │─────►│  Management  │─────►│   Deployment  │        │
│  │  Team    │◄─────│  Dashboard   │◄─────│   Pipeline    │        │
│  └─────────┘      └──────────────┘      └───────┬───────┘        │
│                                                   │                │
│                     Control Actions: Deploy, Config, Scale         │
│                     Feedback: Status, Metrics, Logs                │
│                                                   │                │
│  ┌─────────┐      ┌──────────────┐      ┌───────▼───────┐        │
│  │  End     │─────►│   Frontend   │─────►│   Backend     │        │
│  │  User    │◄─────│   (UI)       │◄─────│   Services    │        │
│  └─────────┘      └──────────────┘      └───────┬───────┘        │
│                                                   │                │
│                     Control Actions: CRUD, Auth, Query             │
│                     Feedback: Response, Status, Data               │
│                                                   │                │
│                                           ┌───────▼───────┐       │
│                                           │   Database &   │       │
│                                           │   Storage      │       │
│                                           └───────────────┘       │
└───────────────────────────────────────────────────────────────────┘
```

### 4.3 Control Actions & Feedback

| Controller | Controlled Process | Control Actions | Feedback |
|-----------|-------------------|----------------|----------|
| End User | Frontend UI | Click, Input, Navigate | Display, Response, Error msg |
| Frontend | Backend API | HTTP Request, Auth Token | HTTP Response, Data |
| Backend | Database | Query, Insert, Update, Delete | Result set, Status, Error |
| Admin | Deployment Pipeline | Deploy, Rollback, Config | Build status, Metrics |
| Pipeline | Server Infrastructure | Start, Stop, Scale | Health check, Logs |

## 5. Step 3: Identify Unsafe Control Actions (UCAs)

### 5.1 Four Types of UCAs

| Type | Mô tả | Ví dụ |
|------|--------|-------|
| **Not providing** | Control action cần nhưng không được thực hiện | Backend không validate input |
| **Providing causes hazard** | Control action được thực hiện nhưng gây hazard | Backend xóa data khi không nên |
| **Wrong timing/order** | Control action quá sớm, quá muộn, sai thứ tự | Auth check sau khi đã trả data |
| **Stopped too soon/applied too long** | Control action dừng quá sớm hoặc kéo dài quá lâu | Session không expire |

### 5.2 UCA Analysis Template

| Control Action | Not Providing | Providing Causes Hazard | Wrong Timing/Order | Stopped Too Soon / Applied Too Long |
|---------------|--------------|------------------------|-------------------|-------------------------------------|
| **Backend validates input** | UCA-1: Backend không validate → invalid data vào DB [H-4] | UCA-2: Validation quá restrictive → reject valid data [H-3] | UCA-3: Validation sau khi data đã được xử lý [H-1, H-4] | UCA-4: Validation chỉ check một phần fields [H-4] |
| **Backend authenticates user** | UCA-5: Không yêu cầu auth → unauthorized access [H-2] | UCA-6: Auth block legitimate user → DoS [H-3] | UCA-7: Auth check delay → race condition [H-2] | UCA-8: Session không timeout → prolonged access [H-2] |
| **Backend writes to DB** | UCA-9: Không write → data loss [H-4] | UCA-10: Write wrong data → corruption [H-1, H-4] | UCA-11: Write out of order → inconsistency [H-4] | UCA-12: Write transaction timeout quá sớm → partial write [H-4] |
| **Pipeline deploys code** | UCA-13: Không deploy → users trên old version [H-3] | UCA-14: Deploy buggy code → system failure [H-1, H-3] | UCA-15: Deploy during peak → downtime [H-3] | UCA-16: Rollback quá chậm → extended outage [H-3] |

### 5.3 Controller Constraints (từ UCAs)

| UCA | Controller Constraint |
|-----|----------------------|
| UCA-1 | Backend MUST validate all input before processing |
| UCA-5 | Backend MUST authenticate user before any data access |
| UCA-8 | Backend MUST enforce session timeout ≤ 30 minutes |
| UCA-10 | Backend MUST verify data integrity before DB write |
| UCA-14 | Pipeline MUST NOT deploy without passing all tests |

## 6. Step 4: Identify Loss Scenarios

### 6.1 Hai loại Loss Scenarios

**Type 1**: Tại sao UCA xảy ra?
- Controller process model sai
- Controller nhận feedback sai
- Controller algorithm sai
- Controller bị compromise

**Type 2**: Tại sao control action không được thực hiện đúng (dù controller đã ra lệnh đúng)?
- Actuator failure (execution failure)
- Communication failure
- Controlled process không phản hồi đúng
- Feedback bị delay/incorrect

### 6.2 Loss Scenario Template

| UCA | Scenario Type | Loss Scenario | Causal Factor | Safety Requirement |
|-----|--------------|---------------|---------------|-------------------|
| UCA-1 (No input validation) | Type 1 | Developer quên implement validation cho new field | Inadequate dev process | REQ: All new fields must have validation tests |
| UCA-1 | Type 1 | Validation logic có bug, return true cho invalid input | Software defect | REQ: Validation must have 100% test coverage |
| UCA-1 | Type 2 | Validation middleware bị bypass do routing config | Configuration error | REQ: Middleware pipeline must be tested end-to-end |
| UCA-5 (No authentication) | Type 1 | Auth service down, system defaults to "allow" | Fail-open design | REQ: System must fail-closed when auth unavailable |
| UCA-5 | Type 2 | Auth token bị intercepted in transit | Communication security | REQ: All auth tokens must use TLS encryption |
| UCA-14 (Deploy buggy code) | Type 1 | Tests pass but don't cover edge case | Inadequate test coverage | REQ: Deploy requires ≥90% code coverage |
| UCA-14 | Type 2 | CI pipeline skips test step due to timeout | Pipeline configuration | REQ: Pipeline must not deploy if any step fails |

## 7. Phân tích STPA dự án CleanBox (Project Analysis)

### 7.1 Step 1: Losses & Hazards — CleanBox

#### Losses

| ID | Loss | Mô tả |
|----|------|-------|
| L-1 | Mất dữ liệu người dùng | Files/folders quan trọng bị xóa không thể phục hồi |
| L-2 | Mất config/settings | App settings reset, cleanup list mất |
| L-3 | Mất khả năng giám sát | Storage monitor không hoạt động → hết dung lượng bất ngờ |
| L-4 | Mất khả năng tương tác | User không thể control app (tray crash, UI freeze) |
| L-5 | Mất tài nguyên hệ thống | App chiếm quá nhiều RAM/CPU → ảnh hưởng hệ thống |

#### System-level Hazards

| ID | Hazard | Related Losses |
|----|--------|---------------|
| H-1 | CleanBox xóa dữ liệu ngoài phạm vi cho phép | L-1 |
| H-2 | CleanBox không phát hiện ổ đĩa gần đầy | L-3 |
| H-3 | CleanBox trở nên unresponsive hoặc crash | L-4, L-5 |
| H-4 | CleanBox lưu trữ config sai / mất config | L-2 |
| H-5 | CleanBox tiêu tốn quá nhiều system resources | L-5 |

#### System-level Safety Constraints

| ID | Safety Constraint | Related Hazard |
|----|------------------|----------------|
| SC-1 | CleanBox CHỈ ĐƯỢC xóa files trong directories mà user đã explicitly approved | H-1 |
| SC-2 | CleanBox PHẢI confirm với user trước mọi destructive action | H-1 |
| SC-3 | CleanBox PHẢI phát hiện và thông báo khi bất kỳ drive nào < threshold | H-2 |
| SC-4 | CleanBox PHẢI duy trì responsive UI và recover từ crashes | H-3 |
| SC-5 | CleanBox PHẢI đảm bảo data integrity cho config file | H-4 |
| SC-6 | CleanBox PHẢI sử dụng < 50MB RAM và < 1% CPU trung bình | H-5 |

### 7.2 Step 2: Control Structure — CleanBox

```
┌───────────────────────────────────────────────────────────────────────┐
│                         CleanBox System                                │
│                                                                        │
│  ┌──────────┐                                                         │
│  │   USER   │                                                         │
│  │          │                                                         │
│  └────┬─────┘                                                         │
│       │ CA: Click buttons, add/remove dirs, change settings           │
│       │ FB: UI display, toast notifications, tray menu                │
│       ▼                                                               │
│  ┌─────────────────┐    signals    ┌──────────────────┐              │
│  │   UI Layer       │◄────────────►│   App Controller  │              │
│  │  (MainWindow,    │              │   (app.py)        │              │
│  │   TrayIcon,      │              │                   │              │
│  │   Views)         │              │   Process Model:  │              │
│  └─────────────────┘              │   - cleanup_dirs  │              │
│                                    │   - thresholds    │              │
│       CA: start/stop cleanup,      │   - auto_start    │              │
│           configure monitors       │   - drive_states  │              │
│       FB: progress, results,       └────────┬─────────┘              │
│           drive status                      │                         │
│                                    ┌────────┼─────────┐              │
│                          ┌─────────┤        │         ├──────────┐   │
│                          ▼         ▼        ▼         ▼          ▼   │
│                    ┌──────────┐ ┌───────┐ ┌───────┐ ┌──────┐ ┌─────┐│
│                    │Cleanup   │ │Storage│ │Notif  │ │Folder│ │Conf ││
│                    │Service   │ │Monitor│ │Service│ │Scan  │ │Mgr  ││
│                    │          │ │       │ │       │ │      │ │     ││
│                    │CA: delete│ │CA:poll│ │CA:show│ │CA:   │ │CA:  ││
│                    │  files,  │ │ drives│ │ toast │ │scan  │ │read/││
│                    │  empty   │ │       │ │       │ │dirs  │ │write││
│                    │  recycle │ │FB:    │ │FB:    │ │      │ │     ││
│                    │          │ │ drive │ │ shown │ │FB:   │ │FB:  ││
│                    │FB:result │ │ info  │ │ status│ │sizes │ │data ││
│                    └────┬─────┘ └───┬───┘ └───────┘ └──┬───┘ └──┬──┘│
│                         │          │                    │        │   │
│                         ▼          ▼                    ▼        ▼   │
│                    ┌─────────────────────────────────────────────────┐│
│                    │           Windows OS / File System               ││
│                    │  (Drives, Registry, Recycle Bin, AppData)        ││
│                    └─────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────┘
```

### 7.3 Step 3: Unsafe Control Actions (UCAs) — CleanBox

#### Controller: App Controller (app.py)

| Control Action | Not Providing (causes hazard) | Providing Causes Hazard | Wrong Timing/Order | Stopped Too Soon / Too Long |
|---------------|------------------------------|------------------------|-------------------|----------------------------|
| **Start Cleanup** | UCA-1: Không cleanup khi user yêu cầu → space không freed [H-2] | UCA-2: Cleanup directories chứa data quan trọng → data loss [H-1] | UCA-3: Cleanup trong khi config đang update → race condition [H-4] | UCA-4: Cleanup stopped giữa chừng → partial delete, inconsistent state [H-1] |
| **Save Config** | UCA-5: Không save setting changes → lost on restart [H-4] | UCA-6: Save config sai format → corrupt file [H-4] | UCA-7: Save config trong khi cleanup đang đọc dirs → race [H-1, H-4] | UCA-8: Save quá frequent (mỗi keystroke) → I/O overhead [H-5] |
| **Start Monitoring** | UCA-9: Không start monitor → no low-space detection [H-2] | UCA-10: Monitor poll quá thường → CPU spike [H-5] | UCA-11: Monitor start trước config load → sai threshold [H-2] | UCA-12: Monitor stop sau config change → stale threshold [H-2] |
| **Show Notification** | UCA-13: Không show notification khi disk critical → user unaware [H-2] | UCA-14: Show notification spam → user disables app [H-3] | UCA-15: Show notification quá trễ (sau disk full) → useless [H-2] | — |

#### Controller: UI Layer (MainWindow, TrayIcon)

| Control Action | Not Providing | Providing Causes Hazard | Wrong Timing/Order | Stopped Too Soon / Too Long |
|---------------|--------------|------------------------|-------------------|----------------------------|
| **Add Directory to list** | — | UCA-16: Cho phép add system folder → sẽ bị xóa [H-1] | — | — |
| **Remove Directory** | — | UCA-17: Remove directory đang cleanup → undefined behavior [H-1, H-3] | — | — |
| **Display Cleanup Progress** | UCA-18: Không show progress → user cancels/force kills [H-3] | — | UCA-19: Progress update sau khi cleanup xong → stale UI [H-3] | — |

### 7.4 Controller Constraints (từ UCAs)

| UCA | Controller Constraint | Priority |
|-----|----------------------|----------|
| UCA-2 | App PHẢI validate cleanup directories against whitelist trước khi xóa | 🔴 Critical |
| UCA-16 | UI KHÔNG ĐƯỢC cho phép add protected system directories | 🔴 Critical |
| UCA-3/7 | App PHẢI sử dụng mutex/lock khi truy cập config đồng thời | 🟠 High |
| UCA-5 | App PHẢI save config ngay sau mỗi user change | 🟠 High |
| UCA-6 | App PHẢI validate config schema trước khi write | 🟠 High |
| UCA-9/11 | App PHẢI start monitor SAU KHI config load hoàn tất | 🟠 High |
| UCA-13 | App PHẢI show notification khi drive < threshold | 🟠 High |
| UCA-14 | App PHẢI rate-limit notifications (max 1 per drive per 24h) | 🟡 Medium |
| UCA-18 | UI PHẢI show progress trong suốt quá trình cleanup | 🟡 Medium |

### 7.5 Step 4: Loss Scenarios — CleanBox

| UCA | Scenario Type | Loss Scenario | Causal Factor | Safety Requirement |
|-----|--------------|---------------|---------------|-------------------|
| UCA-2 | Type 1 | App controller's process model chứa config dirs có system folder → cleanup xóa system files | User thêm nhầm, config không validate | REQ-1: Maintain PROTECTED_PATHS whitelist, check before cleanup |
| UCA-2 | Type 2 | CleanupService nhận đúng dirs nhưng xóa thêm parent dir do path traversal bug | Code bug trong path handling | REQ-2: Strict path normalization + containment check |
| UCA-3 | Type 1 | App bắt đầu cleanup dựa trên stale config (config vừa bị update bởi UI) | No synchronization giữa config read/write | REQ-3: Config read phải acquire shared lock |
| UCA-6 | Type 1 | Config save ghi partial JSON do power loss | Non-atomic file write | REQ-4: Atomic write (temp + rename) |
| UCA-9 | Type 1 | Monitor không start vì QTimer create fails silently | Qt error suppressed | REQ-5: Verify timer.isActive() after start |
| UCA-13 | Type 2 | Notification gửi nhưng win11toast fails silently | Library bug, Windows notification center disabled | REQ-6: Fallback notification via QSystemTrayIcon |
| UCA-16 | Type 1 | UI cho phép add "C:\Windows" vì không có validation | Missing input validation | REQ-7: UI validate against PROTECTED_PATHS trước add |

### 7.6 Safety Requirements Register — CleanBox

| Req ID | Requirement | Source UCA | Priority | Implementation | Verification |
|--------|------------|-----------|----------|---------------|-------------|
| REQ-1 | Maintain PROTECTED_PATHS whitelist, reject cleanup of protected dirs | UCA-2 | 🔴 Critical | constants.py: PROTECTED_PATHS list | Unit test: cleanup protected → exception |
| REQ-2 | Normalize all paths, prevent path traversal | UCA-2 | 🔴 Critical | os.path.realpath + containment check | Unit test: "../" paths → rejected |
| REQ-3 | Acquire lock before reading config for cleanup | UCA-3, UCA-7 | 🟠 High | threading.RLock in ConfigManager | Integration test: concurrent read/write |
| REQ-4 | Atomic config write (temp + rename) | UCA-6 | 🟠 High | Write .tmp → os.replace() | Unit test: interrupt → file intact |
| REQ-5 | Verify QTimer active after start | UCA-9 | 🟠 High | Assert timer.isActive() in start() | Unit test: mock timer failure → retry |
| REQ-6 | Fallback notification when toast fails | UCA-13 | 🟠 High | Try toast → except → tray.showMessage() | Unit test: mock toast error → fallback |
| REQ-7 | UI validates directory against whitelist before add | UCA-16 | 🔴 Critical | Check in CleanupView.add_directory() | E2E test: add system dir → warning |
| REQ-8 | Rate-limit notifications per drive | UCA-14 | 🟡 Medium | Per-drive timestamp dict + 24h cooldown | Unit test: rapid alerts → 1 per 24h |
| REQ-9 | Show progress UI during entire cleanup | UCA-18 | 🟡 Medium | Progress dialog with cancel button | E2E test: progress shown → updated |

## 8. Kế hoạch triển khai và xác minh STPA (Implementation & Verification Plan)

### 8.1 Traceability Matrix

```
L-1 (Data loss)    → H-1 → SC-1,SC-2 → UCA-2,UCA-16  → REQ-1,REQ-2,REQ-7
L-2 (Config loss)  → H-4 → SC-5      → UCA-5,UCA-6,7 → REQ-3,REQ-4
L-3 (No monitoring)→ H-2 → SC-3      → UCA-9,UCA-13  → REQ-5,REQ-6,REQ-8
L-4 (No control)   → H-3 → SC-4      → UCA-18        → REQ-9
L-5 (Resources)    → H-5 → SC-6      → UCA-10        → (existing: 60s interval)
```

### 8.2 Implementation Phases

| Phase | Requirements | Description | Verification |
|-------|-------------|-------------|-------------|
| **Phase 1** (v1.1.0) | REQ-1, REQ-2, REQ-7 | Data protection (whitelist + path validation) | Unit: 20+ test cases cho protected paths; E2E: full flow |
| **Phase 2** (v1.1.0) | REQ-3, REQ-4 | Config integrity (locking + atomic write) | Unit: concurrent access; Integration: crash simulation |
| **Phase 3** (v1.2.0) | REQ-5, REQ-6, REQ-8 | Monitoring reliability (timer verify + notification fallback) | Unit: mock failures → fallback works |
| **Phase 4** (v1.2.0) | REQ-9 | UI responsiveness (progress + cancel) | E2E: progress shown during cleanup |

### 8.3 Verification Strategy

| Level | Target | Method | Coverage Goal |
|-------|--------|--------|--------------|
| **Requirement-level** | Mỗi REQ có ≥ 1 test | pytest marking `@pytest.mark.safety` | 100% REQs covered |
| **UCA-level** | Mỗi UCA type covered | Boundary testing + negative testing | All 4 UCA types per control action |
| **Scenario-level** | Top 10 loss scenarios | Integration tests + chaos testing | P(scenario) < 0.01 after mitigation |
| **System-level** | SC-1 through SC-6 verified | E2E tests + performance benchmarks | All constraints met |

### 8.4 Continuous Safety Monitoring

| Activity | Frequency | Tool | Owner |
|----------|-----------|------|-------|
| STPA re-analysis | Mỗi major feature | Manual review | Tech Lead |
| Safety test suite | Every PR (CI/CD) | GitHub Actions + pytest | Automated |
| Control structure update | When architecture changes | Manual documentation | Architect |
| UCA review | Mỗi sprint retrospective | Team discussion | Team |

## 9. STPA Output Summary

### 7.1 Traceability Matrix

```
Losses → Hazards → Safety Constraints → UCAs → Loss Scenarios → Safety Requirements
  L-1       H-1          SC-1           UCA-1     LS-1,2,3         REQ-1,2,3
  L-2       H-2          SC-2           UCA-5     LS-4,5           REQ-4,5
  ...
```

### 7.2 Safety Requirements Register

| Req ID | Requirement | Source UCA | Priority | Implementation | Verification |
|--------|------------|-----------|----------|---------------|-------------|
| REQ-1 | All input must be validated against schema | UCA-1 | High | Input validation middleware | Unit tests + integration tests |
| REQ-2 | System must fail-closed when auth unavailable | UCA-5 | Critical | Circuit breaker pattern | Chaos testing |
| REQ-3 | Deploy requires all tests passing | UCA-14 | Critical | CI pipeline gate | Pipeline integration test |

## 10. Ưu điểm và Hạn chế

### Ưu điểm
- ✅ Thiết kế cho software-intensive systems
- ✅ Phân tích interactions, không chỉ component failures
- ✅ Xử lý được human factors và organizational issues
- ✅ Không giả định về failure mechanism
- ✅ Tạo ra safety requirements cụ thể, actionable
- ✅ Phát hiện được hazards mà FMEA/FTA bỏ sót
- ✅ Scalable cho hệ thống phức tạp

### Hạn chế
- ❌ Yêu cầu hiểu sâu về systems thinking
- ❌ Tốn thời gian cho hệ thống lớn
- ❌ Ít quantitative (không tính probability trực tiếp)
- ❌ Phụ thuộc vào chất lượng control structure model
- ❌ Ít phổ biến hơn FMEA/FTA → ít công cụ hỗ trợ
- ❌ Cần training cho team

## 11. Tiêu chuẩn tham chiếu

| Tiêu chuẩn | Mô tả |
|-------------|-------|
| STPA Handbook (2018) | Official STPA handbook by Nancy Leveson & John Thomas |
| ISO 21448 (SOTIF) | Safety of the Intended Functionality — references STPA |
| SAE J3187 | STPA for automotive |
| ISO 26262 | Functional safety — STPA as complementary method |
| DO-178C / DO-254 | Aviation software — STPA gaining traction |

## 12. Tài liệu tham khảo

1. Leveson, N. (2012) - "Engineering a Safer World: Systems Thinking Applied to Safety" (MIT Press)
2. Leveson, N. & Thomas, J. (2018) - "STPA Handbook"
3. Thomas, J. (2013) - "Extending and automating a systems-theoretic hazard analysis for requirements generation and analysis" (PhD thesis, MIT)
4. Abdulkhaleq, A. & Wagner, S. (2015) - "XSTAMPP: An eXtensible STAMP Platform as Tool Support for Safety Engineering"
5. Fleming, C.H. (2015) - "Safety-Driven Early Concept Analysis and Development" (PhD thesis, MIT)
