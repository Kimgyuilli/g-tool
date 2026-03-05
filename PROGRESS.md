# 진행 기록

> v1 (Phase 0~5) 기록 아카이브: [PROGRESS_V1.md](./PROGRESS_V1.md)

## 2026-03-05 — agent (Phase 18: 메일 분류 시스템 최적화)
### 완료한 작업
**1단계: 토큰 최적화 + JSON 안정성**
- `backend/app/mail/services/classifier.py`:
  - OpenAI Structured Outputs 적용 (`response_format` json_schema) — JSON 파싱 실패율 0%
  - `_extract_json()` 함수 제거 (불필요)
  - `SYSTEM_PROMPT` 마지막 줄 JSON 지시 제거 (~20토큰 절감)
  - `SINGLE_TEMPLATE`, `BATCH_TEMPLATE`에서 JSON 형식 지시 제거
  - `_truncate_body` default 500→300자 (~50토큰/메일 절감)
  - `chunk_size` 10→15 (API 호출 33% 감소)

**2단계: 병렬 처리**
- `backend/app/mail/services/classifier.py`:
  - `_process_chunk()` 함수 분리 (청크별 독립 처리)
  - `asyncio.as_completed()` + `asyncio.Semaphore(3)`로 병렬 처리
  - `on_progress` 콜백 파라미터 추가

**3단계: SSE 실시간 진행 피드백**
- `backend/app/mail/routers/classify.py`:
  - `POST /api/classify/mails` → SSE `StreamingResponse` 변경
  - progress/done/error 이벤트 형식
- `frontend/src/features/mail/hooks/useMailActions.ts`:
  - `handleClassify` fetch streaming으로 변경 (native ReadableStream)
  - `classifyProgress` 상태 추가 (`{processed, total} | null`)
- `frontend/src/components/AppHeader.tsx`:
  - `classifyProgress` prop 추가
  - 분류 버튼에 "분류 중 15/45" 텍스트 + 하단 프로그레스 바 표시
- `frontend/src/app/page.tsx`:
  - `classifyProgress` prop 전달

### 검증
- `uv run ruff check .` — All checks passed
- `pnpm lint` — 통과
- `pnpm build` — 빌드 성공

### 다음 할 일
- ~~커밋 + PR 생성~~ → PR #10 완료
- 수동 테스트: 분류 버튼 클릭 → 진행률 표시 → 분류 완료 확인
- PR 리뷰 후 main 병합

### 이슈/참고
- Structured Outputs의 json_schema는 최상위가 object여야 하므로 batch 응답을 `{"results": [...]}` 형태로 감쌈
- SSE 이벤트는 classify_batch 완료 후 일괄 전송 (on_progress 콜백이 동기이므로 큐에 모아둠)
- 외부 라이브러리 추가 없음 (asyncio.Semaphore, native fetch ReadableStream)

## 2026-03-05 — agent (Phase 17: 프로젝트 리네이밍 Mail Organizer → G-Tool)
### 완료한 작업
- **코드**: `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/core/exceptions.py`, `backend/app/config.py` (DB명 `gtool.db`), `docker-compose.yml`
- **프론트엔드**: `layout.tsx`, `AppHeader.tsx`, `LoginScreen.tsx` — 타이틀/설명 변경
- **테스트**: `smoke.test.tsx`, `LoginScreen.test.tsx` — "G-Tool"로 변경
- **에이전트**: `.claude/agents/` 5개 파일 — "G-Tool 프로젝트"로 변경
- **문서**: `CLAUDE.md`, `DEPLOY.md`, `references/guide-google-oauth-setup.md`, `references/guide-oracle-cloud-free-deploy.md`
- **CI/CD**: `.github/workflows/deploy.yml` — `cd ~/g-tool`
- **메모리**: `MEMORY.md` — "G-Tool"로 변경

### 검증
- `uv run ruff check .` — All checks passed
- `pnpm lint` — 통과
- `pnpm build` — 빌드 성공
- `pnpm test` — 35/35 통과
- `grep "Mail Organizer"` 잔여 — 없음 (PROGRESS.md 과거 기록 제외)

### 다음 할 일
- 커밋 + PR → main 병합
- main 병합 후: `gh repo rename g-tool`
- 배포 서버: `mv ~/-mail-organizer ~/g-tool`, `mv mail_organizer.db gtool.db`

### 이슈/참고
- PROGRESS.md 과거 기록은 수정하지 않음 (히스토리 보존)
- GitHub repo rename 시 기존 URL은 자동 redirect됨

## 2026-03-05 — agent (Phase 16: 캘린더 일정 삭제 기능 추가)
### 완료한 작업
- `backend/app/calendar/service.py`: `delete_event` 함수 추가 (기존 `_build_calendar` + `asyncio.to_thread` 패턴)
- `backend/app/calendar/router.py`: `DELETE /api/calendar/events/{event_id}?calendar_id=...` 엔드포인트 추가, `delete_event` import
- `frontend/src/features/calendar/hooks/useCalendar.ts`: `deleteEvent` 함수 추가 (DELETE 호출 + loadEvents 갱신), return에 포함
- `frontend/src/features/calendar/components/CalendarEventDetail.tsx`: `onDelete` prop 추가, 헤더에 Trash2 삭제 버튼 배치 (deleting 시 Loader2 spinner + disabled)
- `frontend/src/features/calendar/CalendarPage.tsx`: `deleteEvent` destructure, `handleDeleteEvent` 핸들러 (삭제 → toast → selectedEvent null), `onDelete` prop 전달

### 검증
- `uv run ruff check .` — All checks passed
- ESLint — 통과
- `next build` — 빌드 성공

### 다음 할 일
- 커밋 + PR 생성

### 이슈/참고
- 없음

## 2026-03-05 — agent (Phase 15: 캘린더 동기화 버튼 추가)
### 완료한 작업
- `frontend/src/features/calendar/components/CalendarSidebar.tsx`: `onRefresh`, `refreshing` props 추가, "오늘" 버튼 옆에 RefreshCw 동기화 버튼 배치, refreshing 시 animate-spin + disabled
- `frontend/src/features/calendar/CalendarPage.tsx`: `refreshing` state + `handleRefresh` 함수 추가 (loadCalendars → loadEvents → toast 알림), CalendarSidebar에 props 전달

### 검증
- ESLint — 통과
- `next build` — 빌드 성공

### 다음 할 일
- 커밋 + PR 생성

### 이슈/참고
- `.next/dev/types/routes.d.ts` 캐시 파일 빌드 에러 → `.next` 삭제 후 클린 빌드로 해결

## 2026-03-05 — agent (Phase 14: 북마크 기능 추가)
### 완료한 작업
**백엔드 (14-1)**
- `backend/app/bookmark/__init__.py`: 패키지 초기화
- `backend/app/bookmark/models.py`: BookmarkCategory, Bookmark SQLAlchemy 모델 (Mapped[] 스타일, Index, SET NULL on category delete)
- `backend/app/bookmark/schemas.py`: Pydantic 스키마 (CategoryCreate, CategoryResponse, BookmarkCreate, BookmarkUpdate, BookmarkResponse, URL 자동 https:// 보정)
- `backend/app/bookmark/service.py`: async CRUD (소유권 검증, favicon 자동 생성, position 자동 계산, bookmark_count 서브쿼리)
- `backend/app/bookmark/router.py`: `/api/bookmark` 라우터 (7개 엔드포인트: 카테고리 3 + 북마크 4)
- `backend/app/main.py`: bookmark_router 등록

**프론트엔드 (14-2)**
- `frontend/src/features/bookmark/types.ts`: Bookmark, BookmarkCategory 인터페이스 + 색상 상수
- `frontend/src/features/bookmark/hooks/useBookmarks.ts`: 카테고리+북마크 CRUD 훅 (낙관적 업데이트)
- `frontend/src/features/bookmark/BookmarkContext.tsx`: Context Provider (prop drilling 방지, 모달 상태 관리)
- `frontend/src/features/bookmark/BookmarkPage.tsx`: 사이드바 + 그리드 레이아웃
- `frontend/src/features/bookmark/components/BookmarkCard.tsx`: 카드 (favicon, 제목, URL, 카테고리 뱃지, 수정/삭제)
- `frontend/src/features/bookmark/components/BookmarkGrid.tsx`: 반응형 카드 그리드 (grid-cols-1 sm:2 lg:3 xl:4)
- `frontend/src/features/bookmark/components/BookmarkCategorySidebar.tsx`: 카테고리 사이드바 (전체/미분류 필터, 카테고리 목록)
- `frontend/src/features/bookmark/components/AddBookmarkModal.tsx`: 북마크 생성/수정 Dialog (key 패턴으로 setState-in-effect 해결)
- `frontend/src/features/bookmark/components/AddCategoryModal.tsx`: 카테고리 생성 Dialog (색상 선택)
- `frontend/src/components/AppHeader.tsx`: 북마크 탭 추가 (Bookmark 아이콘)
- `frontend/src/app/page.tsx`: activePage 타입에 "bookmark" 추가, BookmarkPage 렌더링

**검증**
- `uv run ruff check .` — All checks passed
- ESLint — 통과
- `next build` — 빌드 성공

### 다음 할 일
- 커밋 + PR 생성
- 수동 테스트: 카테고리 생성 → 북마크 등록 → 카테고리 필터 → 북마크 수정 → 삭제

### 이슈/참고
- ESLint `react-hooks/set-state-in-effect` 룰 → AddBookmarkModal에서 FormFields 별도 컴포넌트 + key 패턴으로 해결
- 카테고리 삭제 시 북마크는 DB의 `ondelete="SET NULL"`로 미분류로 전환
- favicon은 Google Favicon API로 자동 생성 (`https://www.google.com/s2/favicons?domain={domain}&sz=32`)

## 2026-03-05 — agent (Phase 13: Todo 코드 최적화 및 개선)
### 완료한 작업
**백엔드 (6가지 개선)**
- `schemas.py`: status/priority를 `Literal` 타입으로 제한 (잘못된 값 DB 저장 방지)
- `schemas.py`: `ReorderRequest.items`를 `list[dict]` → `list[ReorderItem]` 타입 안전화
- `schemas.py`: `due_date` 파싱을 `field_validator`로 schema 레벨로 이동
- `schemas.py`: `TaskResponse`, `SubtaskResponse` Pydantic response model 추가
- `service.py`: `reorder_tasks` N+1 쿼리 → `Task.id.in_(ids)` 일괄 조회로 개선
- `service.py`: `update_task` subtask 이중 로드 제거 (`_get_task_or_404`에 `load_subtasks` 파라미터 추가)
- `service.py`: `_task_to_dict`/`_subtask_to_dict` → `_task_to_response`/`_subtask_to_response` (Pydantic 모델 반환)
- `service.py`: `func.max()` 대신 `order_by().limit(1)` 패턴으로 position 조회

**프론트엔드 (6가지 개선)**
- `useTodo.ts`: CUD 낙관적 업데이트 (createTask → 로컬 추가, updateTask → 로컬 교체, deleteTask → 로컬 제거 후 서버 호출)
- `useTodo.ts`/`useSubtasks.ts`: 에러 시 `setTasks([])`/`setSubtasks([])` 제거 → 기존 데이터 보존
- `useSubtasks.ts`: toggleSubtask 낙관적 업데이트 (즉시 UI 반영 → 서버 응답으로 확정)
- `KanbanBoard.tsx`: handleDragEnd 로직 단순화 (이중 필터링/중복 제거 제거)
- `KanbanCard.tsx`: descDraft 동기화 → `DescriptionEditor` 별도 컴포넌트 분리 + key 패턴
- `KanbanCard.tsx`: `dispatchEvent(contextmenu)` → `DropdownMenu` 컴포넌트로 안정적 교체 (⋯ 클릭 → DropdownMenu, 우클릭 → ContextMenu)
- `TodoContext.tsx` 신규: prop drilling 해소 (TodoPage → KanbanBoard → KanbanCard 간 11개 prop → Context)
- `TodoPage.tsx`: 핸들러 함수들 Context로 이동, 코드 95줄 → 15줄로 축소
- `dropdown-menu.tsx`: `DropdownMenuSub`, `DropdownMenuSubTrigger`, `DropdownMenuSubContent` 추가

**검증**
- `uv run ruff check .` — All checks passed
- `pnpm lint` — 통과
- `pnpm build` — 빌드 성공

### 다음 할 일
- 커밋 + PR 업데이트
- 수동 테스트: 낙관적 업데이트 동작, 드래그앤드롭, 컨텍스트 메뉴/드롭다운 메뉴

### 이슈/참고
- ESLint `react-hooks/set-state-in-effect` 룰로 useEffect 내 setState 불가 → DescriptionEditor 분리 + key 패턴으로 해결
- ESLint `react-hooks/refs` 룰로 render 중 ref 업데이트 불가 → 동일 방법으로 우회

## 2026-03-05 — agent (Phase 12: Todo 칸반 보드 리팩토링)
### 완료한 작업
**백엔드**
- `backend/app/todo/models.py`: Project 클래스 삭제, Task에 user_id(FK→users) 추가, status 값 `todo/in_progress/on_hold`, 인덱스 `(user_id, status, position)`
- `backend/app/todo/schemas.py`: ProjectCreate/ProjectUpdate 삭제, TaskCreate/TaskUpdate에서 project_id 제거
- `backend/app/todo/service.py`: Project 함수 5개 + _get_project_or_404 삭제, Task/Subtask에서 project join 제거 → user_id 직접 검증, reorder_tasks에 status 변경 지원
- `backend/app/todo/router.py`: Project 엔드포인트 5개 삭제, `GET /projects/{id}/tasks` → `GET /tasks`

**프론트엔드**
- `frontend/src/features/todo/types.ts`: Project 타입 삭제, Task.status 타입 변경, STATUS_LABELS 추가
- `frontend/src/features/todo/hooks/useTodo.ts`: Project 관련 state/함수 제거, loadTasks → GET /tasks 플랫 조회, reorderTasks 함수 추가
- `frontend/src/features/todo/components/KanbanBoard.tsx`: @dnd-kit 기반 3열 칸반 보드 (todo/in_progress/on_hold), 드래그앤드롭 컬럼 이동, 퀵 추가 입력
- `frontend/src/features/todo/components/KanbanCard.tsx`: useSortable 드래그 가능 카드, 인라인 확장 (설명 편집 + 서브태스크 관리)
- `frontend/src/features/todo/TodoPage.tsx`: ProjectSidebar/TaskDetailView/ResizablePanelGroup 제거, KanbanBoard만 렌더링
- 삭제: ProjectSidebar.tsx, TaskListView.tsx, TaskDetailView.tsx
- @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities 설치

**검증**
- `uv run ruff check .` — All checks passed
- `pnpm lint` — 통과
- `pnpm build` — 빌드 성공

### 다음 할 일
- DB 파일 삭제 후 재시작 (tasks 테이블 스키마 변경)
- 수동 테스트: 칸반 보드 드래그앤드롭, 태스크 생성/삭제, 서브태스크 관리

### 이슈/참고
- SQLite 컬럼 변경 불가 → 개발 DB 파일 삭제 후 재생성 필요
- projects 테이블은 DB에 남아있어도 무해 (코드에서 참조하지 않음)

## 2026-03-04 — agent (Phase 11: TodoList 기능 추가)
### 완료한 작업
**백엔드 (11-1)**
- `backend/app/todo/__init__.py`: 패키지 초기화
- `backend/app/todo/models.py`: Project, Task, Subtask SQLAlchemy 모델 (Mapped[] 스타일, 인덱스, CASCADE)
- `backend/app/todo/schemas.py`: Pydantic 요청 모델 (Create, Update, Reorder)
- `backend/app/todo/service.py`: async CRUD 비즈니스 로직 (소유권 검증, position 자동 계산)
- `backend/app/todo/router.py`: `/api/todo` 라우터 (15개 엔드포인트)
- `backend/app/main.py`: todo_router 등록

**프론트엔드 (11-2)**
- `frontend/src/features/todo/types.ts`: Project, Task, Subtask 인터페이스 + 요청/응답 타입
- `frontend/src/features/todo/hooks/useTodo.ts`: 프로젝트/태스크 CRUD 훅
- `frontend/src/features/todo/hooks/useSubtasks.ts`: 서브태스크 CRUD + 토글 훅
- `frontend/src/features/todo/components/ProjectSidebar.tsx`: 프로젝트 목록, 색상 도트, 생성/삭제
- `frontend/src/features/todo/components/TaskListView.tsx`: 퀵 추가, 체크박스, 우선순위 도트, 마감일
- `frontend/src/features/todo/components/TaskDetailView.tsx`: 설명 편집, 서브태스크 목록, 상태/우선순위 토글
- `frontend/src/features/todo/TodoPage.tsx`: 3-panel 레이아웃 (프로젝트 사이드바 | 태스크 목록 | 태스크 상세)
- `frontend/src/components/ui/checkbox.tsx`: shadcn/ui Checkbox 컴포넌트 추가 (@radix-ui/react-checkbox)
- `frontend/src/components/ui/textarea.tsx`: shadcn/ui Textarea 컴포넌트 추가
- `frontend/src/app/page.tsx`: activePage 타입에 "todo" 추가, TodoPage 조건부 렌더링
- `frontend/src/components/AppHeader.tsx`: 할일 탭 추가 (CheckSquare 아이콘)

**검증**
- `uv run ruff check .` — All checks passed
- `pnpm lint` — 통과
- `pnpm build` — 빌드 성공

### 다음 할 일
- PR 생성 후 main에 병합
- Phase 11-3 (UI 폴리시): 드래그앤드롭 재정렬, 우선순위 선택기, 마감일 date-picker, 상태 필터 탭, 프로젝트 색상 선택기

### 이슈/참고
- shadcn/ui checkbox, textarea 컴포넌트가 없어서 직접 추가함
- SQLite create_all()은 기존 테이블에 영향 없이 새 테이블만 생성
- 기존 DB 재생성 불필요 (새 테이블 추가만)

## 2026-03-04 — agent (Phase 10: DDD 도메인 패키지 분리 완료)
### 완료한 작업
**백엔드 — DDD 패키지 구조**
- `app/core/`: database.py, exceptions.py, dependencies.py, background_sync.py
- `app/auth/`: router.py, service.py, dependencies.py
- `app/calendar/`: router.py, service.py, schemas.py
- `app/mail/`: models.py (4파일 통합), routers/ (gmail, naver, inbox, classify), services/ (gmail, naver, classifier, feedback, helpers)
- 기존 flat 구조 (models/, routers/, services/, dependencies.py, exceptions.py) 완전 삭제
- main.py, conftest.py, test_classify.py import 경로 업데이트
- ruff clean, pytest 24/24 통과

**프론트엔드 — feature 폴더 구조**
- `features/mail/`: components/ (7개), hooks/ (5개), types.ts, constants.ts
- `features/calendar/`: CalendarPage.tsx, components/ (4개), hooks/ (1개), types.ts
- `features/auth/`: components/ (2개), hooks/ (2개), types.ts (UserInfo 분리)
- 공통 유지: components/AppHeader.tsx, Pagination.tsx, ui/
- page.tsx, AppHeader.tsx, 테스트 5개 파일 import 경로 업데이트
- 기존 hooks/, types/, constants/ 디렉토리 삭제
- pnpm lint + pnpm build 통과

### 다음 할 일
- PR 생성 후 main에 병합
- page.tsx → thin shell + MailPage 추출 (선택적 추가 리팩토링)
- 주간/일간 캘린더 뷰 (Phase 9-3 pending)

### 이슈/참고
- CalendarView → CalendarPage로 rename (feature 폴더 관례에 맞춤)
- UserInfo 타입은 features/auth/types.ts로 분리, useMailActions에서 cross-feature import
- MailPage 추출은 AppHeader와의 상태 공유 복잡성으로 인해 추후 진행

## 2026-03-04 — agent (Phase 9-4: 캘린더 이벤트 생성 기능 완료)
### 완료한 작업
**백엔드**
- `backend/app/services/google_auth.py`: OAuth 스코프 `calendar.readonly` → `calendar.events`로 변경, `OAUTHLIB_RELAX_TOKEN_SCOPE=1` 설정 (Google 스코프 순서 불일치 해결)
- `backend/app/services/calendar_service.py`: `create_event()` 함수 추가 (종일/시간 이벤트 분기 처리)
- `backend/app/routers/calendar.py`: `POST /events` 엔드포인트 + `CreateEventRequest` Pydantic 모델

**프론트엔드**
- `frontend/src/types/calendar.ts`: `CreateEventRequest` 타입 추가
- `frontend/src/hooks/useCalendar.ts`: `createEvent` 함수 추가 (POST + 자동 새로고침)
- `frontend/src/components/EventCreateModal.tsx`: 이벤트 생성 모달 (제목, 종일, 날짜/시간, 장소, 설명, 캘린더 선택)
- `frontend/src/components/CalendarView.tsx`: 생성 모달 연동 + toast 알림

**버그 수정**
- Dialog `aria-describedby` 경고 해결 (sr-only DialogDescription 추가)
- 날짜 클릭 시 모달에 해당 날짜가 기본값으로 설정되도록 수정 (useEffect로 open 시 상태 리셋)
### 다음 할 일
- 주간/일간 캘린더 뷰 (Phase 9-3 pending)
- 이벤트 수정/삭제 기능 (추후)
### 이슈/참고
- `OAUTHLIB_RELAX_TOKEN_SCOPE=1`: Google OAuth `include_granted_scopes`로 인해 이전 스코프가 포함되어 순서/내용 불일치 발생 → 이 환경변수로 해결
- 스코프 변경 후 기존 사용자 재인증 필요

## 2026-03-04 — frontend-dev (Google Calendar 이벤트 생성 기능)
### 완료한 작업
- `frontend/src/types/calendar.ts`: CreateEventRequest 타입 추가
- `frontend/src/hooks/useCalendar.ts`: createEvent 함수 추가
  - POST /api/calendar/events 호출
  - 생성 후 이벤트 목록 자동 새로고침
- `frontend/src/components/EventCreateModal.tsx`: 이벤트 생성 모달 컴포넌트 신규 생성
  - Dialog 기반 모달 UI
  - 제목, 종일 여부, 시작/종료 날짜&시간, 장소, 설명, 캘린더 선택
  - 종일 이벤트 vs 시간 이벤트 조건부 입력
  - 유효성 검증 (제목 필수)
- `frontend/src/components/CalendarView.tsx`: 이벤트 생성 기능 연동
  - 사이드바에 "일정 추가" 버튼 추가
  - 날짜 클릭 시 해당 날짜로 생성 모달 오픈 (onSelectDate 핸들러 연결)
  - toast 알림 (성공/실패)
- `PLAN.md`: Phase 9-3에 "이벤트 생성 기능" 태스크 추가, Phase 9-4 백엔드 쓰기 권한 확장 계획 추가
### 다음 할 일
- 백엔드 Calendar API에 POST /events 엔드포인트 구현 필요 (Phase 9-4)
  - OAuth 스코프에 `calendar` (쓰기 권한) 추가
  - calendar_service.py에 create_event, update_event, delete_event 추가
  - routers/calendar.py에 POST /events 라우터 추가
- 프론트엔드에서 이벤트 생성 테스트
### 이슈/참고
- 현재 백엔드는 `calendar.readonly` 스코프만 있어 POST 요청이 실패함 (403 Forbidden 예상)
- 백엔드 9-4 완료 후 재인증 필요 (기존 사용자 로그아웃 → 재로그인으로 새 스코프 동의)

## 2026-03-04 — agent (Phase 9: Google Calendar 통합)
### 완료한 작업
**백엔드 (9-1)**
- `backend/app/services/google_auth.py`: OAuth 스코프에 `calendar.readonly` 추가
- `backend/app/services/calendar_service.py`: Calendar Service 신규 생성 — list_calendars, list_events, get_event, _parse_event
- `backend/app/routers/calendar.py`: Calendar API 라우터 — /calendars, /events, /events/{id}
- `backend/app/main.py`: calendar 라우터 등록

**프론트엔드 구조 변경 (9-2)**
- `frontend/src/components/AppHeader.tsx`: 메일/캘린더 페이지 전환 네비게이션 추가
- `frontend/src/app/page.tsx`: activePage 상태, 조건부 렌더링

**프론트엔드 캘린더 UI (9-3)**
- `frontend/src/types/calendar.ts`: CalendarInfo, CalendarEvent 타입
- `frontend/src/hooks/useCalendar.ts`: 캘린더/이벤트 로드, 월 이동, 필터링 훅
- `frontend/src/components/CalendarMonthView.tsx`: 월간 그리드 뷰
- `frontend/src/components/CalendarEventDetail.tsx`: 이벤트 상세 패널
- `frontend/src/components/CalendarSidebar.tsx`: 캘린더 목록/월 네비게이션
- `frontend/src/components/CalendarView.tsx`: 통합 3-panel 레이아웃
### 다음 할 일
- Google Cloud Console에서 Calendar API 활성화 필요
- 기존 사용자 로그아웃 → 재로그인 (calendar.readonly 스코프 동의 필요)
- 배포 후 통합 테스트
- 주간/일간 뷰는 추후 확장
### 이슈/참고
- 기존 OAuth 토큰은 calendar.readonly 스코프 없음 → 재인증 필수
- prompt="consent"가 이미 설정되어 있어 재로그인 시 자동으로 새 스코프 동의 화면 표시
- DB 모델 변경 없음 (캘린더 데이터는 실시간 API 호출)

## 2026-03-04 — frontend-dev (캘린더 UI 컴포넌트 구현 완료)
### 완료한 작업
- `frontend/src/components/CalendarMonthView.tsx`: 월간 캘린더 뷰 구현
  - 월별 그리드 레이아웃 (일~토, 6주)
  - 이벤트를 날짜별로 그룹핑하여 표시
  - 종일 이벤트 vs 시간 이벤트 구분 표시
  - 일요일(빨강), 토요일(파랑) 색상 구분
  - 오늘 날짜 하이라이트
  - 이벤트 클릭 → 상세 패널 오픈
  - 최대 3개 이벤트 표시, 초과 시 "+N개 더" 표시
- `frontend/src/components/CalendarEventDetail.tsx`: 이벤트 상세 패널
  - 이벤트 제목, 시간, 장소, 참석자, 설명 표시
  - 종일 이벤트 vs 시간 이벤트에 따른 시간 포맷 처리
  - 참석자 응답 상태 표시 (수락/거절/미정)
  - Google Calendar 링크
- `frontend/src/components/CalendarSidebar.tsx`: 캘린더 사이드바
  - 월 네비게이션 (이전/다음/오늘)
  - 캘린더 목록 체크박스 필터링
  - 캘린더별 색상 표시
  - 기본 캘린더 표시
- `frontend/src/components/CalendarView.tsx`: 통합 캘린더 뷰
  - 사이드바 + 월간뷰 + 이벤트 상세 3-panel 레이아웃
  - ResizablePanel로 패널 크기 조절 가능
  - 이벤트 선택 시 상세 패널 동적 표시
- `frontend/src/app/page.tsx`: CalendarView import 및 연동
  - activePage === "calendar" 조건부 렌더링
### 다음 할 일
- 백엔드 Calendar API 라우터 완료 후 통합 테스트
- 주간/일간 캘린더 뷰 (CalendarWeekView.tsx) 추후 구현 (optional)
### 이슈/참고
- 백엔드 API 라우터 `/api/calendar/calendars`, `/api/calendar/events` 구현 대기 중
- useCalendar 훅의 try-catch로 백엔드 미준비 상태에서도 에러 없이 빈 화면 표시

## 2026-03-04 — frontend-dev (Google Calendar 프론트엔드 구조 변경)
### 완료한 작업
- `frontend/src/types/calendar.ts`: Calendar 타입 정의 파일 생성 (CalendarInfo, CalendarEvent, CalendarsResponse, EventsResponse)
- `frontend/src/components/AppHeader.tsx`: 페이지 네비게이션 추가
  - props에 `activePage`, `onPageChange` 추가
  - 로고 옆에 메일/캘린더 전환 탭 추가 (lucide-react Mail, Calendar 아이콘 사용)
  - 소스 필터 탭과 메일 액션 버튼은 `activePage === "mail"` 조건부 렌더링
- `frontend/src/app/page.tsx`: activePage 상태 추가 및 조건부 렌더링
  - `useState<"mail" | "calendar">("mail")` 추가
  - AppHeader에 activePage, onPageChange props 전달
  - 메일 UI (Sheet, NaverConnectModal, 3-panel layout)는 `activePage === "mail"` 조건 내 렌더링
  - 캘린더 페이지는 placeholder div 표시 (캘린더 뷰 구현 대기)
- `frontend/src/hooks/useCalendar.ts`: 캘린더 훅 구현
  - 캘린더 목록 로드, 이벤트 로드 (월 기준)
  - 캘린더 선택/필터링, 월 이동 네비게이션 로직
  - enabled 플래그로 캘린더 페이지 활성화 시에만 API 호출
### 다음 할 일
- 백엔드 Calendar API 라우터 완료 후 프론트엔드 캘린더 뷰 컴포넌트 구현
  - CalendarMonthView.tsx (월간 그리드)
  - CalendarWeekView.tsx (주간/일간 타임라인)
  - CalendarEventDetail.tsx (이벤트 상세)
  - CalendarListSidebar.tsx (캘린더 목록 필터)
### 이슈/참고
- 백엔드 API 라우터 `/api/calendar/calendars`, `/api/calendar/events` 구현 필요
- useCalendar 훅은 백엔드 API 준비 전까지 에러를 조용히 처리 (try-catch)

## 2026-03-04 — agent (HTML 이메일 렌더링)
### 완료한 작업
- `backend/app/models/mail.py`: `body_html` 컬럼 추가 (Text, nullable)
- `backend/app/services/gmail_service.py`: `_extract_body()` → text+html dict 반환, `_parse_message()` 및 sync 함수에서 body_html 저장
- `backend/app/services/naver_service.py`: 동일하게 text+html 동시 추출
- `backend/app/services/helpers.py`: API 응답에 `body_html` 포함
- `frontend/src/components/HtmlEmailRenderer.tsx`: DOMPurify whitelist 기반 안전한 HTML 렌더링 컴포넌트 신규 생성
- `frontend/src/components/MailDetailView.tsx`: body_html 유무에 따른 조건부 렌더링
- `frontend/src/types/mail.ts`: `body_html` 필드 추가
- `frontend/src/app/globals.css`: `@tailwindcss/typography` 플러그인 추가
- `sync_gmail_messages()`에서 `body_html` 저장 누락 버그 수정
- PR #2 생성: https://github.com/Kimgyuilli/-mail-organizer/pull/2
### 다음 할 일
- PR #2 머지 후 배포 확인
- Gmail/Naver HTML 이메일 수동 렌더링 테스트
- AI 분류 재실행 (DB 초기화로 기존 분류 소실됨)
### 이슈/참고
- SQLite `create_all()`은 기존 테이블에 컬럼 추가 불가 — DB 재생성 필요했음
- body_html 테스트 위해 mails 전체 삭제 → Classification CASCADE 삭제됨, 재분류 필요

## 2026-03-02 — agent (CI/CD 파이프라인 구축)
### 완료한 작업
- `.github/workflows/ci.yml`: CI 파이프라인 (backend-lint, backend-test, frontend-lint, frontend-test, frontend-build)
- `.github/workflows/deploy.yml`: CD 파이프라인 (CI 성공 + main push → SSH로 Oracle VM 자동 배포)
- GitHub Secrets 등록: `ORACLE_SSH_KEY`, `ORACLE_HOST`, `ORACLE_USERNAME`
- `frontend/pnpm-workspace.yaml`: `packages` 필드 추가 (CI 호환)
- `CategoryBadge.test.tsx`: small 모드 테스트 수정 (실제 동작에 맞게)
- gh-aw (ci-doctor, pr-fix) 시도 → Copilot Pro 미구독으로 제거
- CI 전체 통과 확인
### 다음 할 일
- CD 자동 배포 검증 (main 머지 → Oracle VM 반영 확인)
- Copilot Pro 구독 시 gh-aw 재도입 검토
### 이슈/참고
- deploy.yml: host/username은 secrets로 관리 (하드코딩 방지)
- pnpm/action-setup@v4에 `version: 9` 명시 (packageManager 필드 미설정 대응)
- gh-aw는 Copilot Pro 이상 구독 필요 (학생/Free 불가)

## 2026-03-02 — Oracle Cloud 배포 완료
### 완료한 작업
- Oracle VM 프로비저닝 성공 (A1.Flex, 춘천 리전)
- Reserved Public IP 적용: `138.2.116.61`
- DNS 설정: `gtool.kro.kr` → `138.2.116.61`
- Docker + Docker Compose 설치
- OS 방화벽 (iptables) + OCI Security List에 80/443 포트 오픈
- `git clone` → 환경변수 설정 → `docker compose up -d --build`
- Caddy Let's Encrypt HTTPS 인증서 자동 발급 완료
- `https://gtool.kro.kr` 접속 확인
### 다음 할 일
- Google OAuth redirect URI 추가 (`https://gtool.kro.kr/api/auth/callback`)
- CI/CD 파이프라인 구축 (GitHub Actions)
### 이슈/참고
- OCI Security List에 80/443 Ingress Rule 누락으로 ACME challenge 실패 → 추가 후 해결
- Keep-alive crontab 설정 권장 (OCI idle VM 회수 방지)

## 2026-03-02 — backend-dev (Oracle Cloud 인프라 셋업)
### 완료한 작업
- OCI API Key 생성 + `~/.oci/config` 설정 완료
- Terraform 설정 파일 작성 (`infra/main.tf`) — A1.Flex, 2 OCPU, 12GB
- `terraform init` + `terraform plan` 성공 확인
- SSH 키 생성 (`~/.ssh/oracle_cloud`)
- 도메인 확보: `gtool.kro.kr`
- DEPLOY.md 배포 가이드 작성
- OCI Compartment `g-tool` 생성, VCN + Security List 설정 완료
### 다음 할 일
- `terraform apply` 재시도 (춘천 리전 ARM capacity 부족으로 blocked)
  - 새벽 시간대(KST 2~6시) 시도 권장
  - 명령어: `cd infra && terraform apply -auto-approve`
- VM 생성 성공 후 → DEPLOY.md Step 3(Docker 설치)부터 진행
- DNS A 레코드에 VM Public IP 연결 (`gtool.kro.kr`)
- Google OAuth redirect URI 추가: `https://gtool.kro.kr/api/auth/callback`
### 이슈/참고
- OCI 춘천 리전 ARM(A1.Flex) capacity 부족 — "Out of host capacity" 에러
- Terraform, OCI API 인증은 모두 정상 동작 확인됨
- `infra/` 디렉토리는 .gitignore 처리 (OCID 등 민감정보 포함)

## 2026-03-02 — backend-dev (Oracle Cloud 배포 코드 작업)
### 완료한 작업
- `backend/app/config.py`: `frontend_url` 설정 추가
- `backend/app/main.py`: CORS origins를 `settings.frontend_url`에서 읽도록 변경
- `backend/app/routers/auth.py`: OAuth 콜백 리다이렉트 URL을 `settings.frontend_url` 사용
- `frontend/next.config.ts`: `output: "standalone"` 추가
- `backend/Dockerfile`: Python 3.13-slim + uv 기반
- `frontend/Dockerfile`: Multi-stage build (deps → build → production)
- `docker-compose.yml`: backend + frontend + Caddy (리버스 프록시 + 자동 HTTPS)
- `Caddyfile`: `/api/*` → backend, `/*` → frontend
- `.dockerignore` (backend, frontend 각각)
- `backend/.env.example` 업데이트 (FRONTEND_URL 추가)
- `.env.production.example` 생성 (DOMAIN 설정)
- `.gitignore`에 `.env.production` 추가
### 다음 할 일
- Oracle Cloud VM 프로비저닝 (ARM, Free Tier)
- 서버에서 `docker compose up -d`로 배포
- DNS 설정 후 HTTPS 자동 발급 확인
### 이슈/참고
- SQLite 유지 (1인 사용, 볼륨 마운트로 영속)
- 로컬 개발 플로우 변경 없음 (`uv run fastapi dev`, `pnpm dev` 그대로)
- Caddy가 `/api` prefix를 strip하므로 프론트에서 API 호출 시 `/api/...` 경로 사용

## 2026-03-02 — planner (v1 release 정리 및 v2 준비)
### 완료한 작업
- v1 아카이브: PLAN_V1.md, PROGRESS_V1.md 생성
- PLAN.md, PROGRESS.md를 v2 시작점으로 초기화
- references/ 정리 — 구현 완료된 조사 자료 5개 삭제, 2개 유지
- CLAUDE.md 업데이트 — 로드맵 완료 표시, 프로젝트 구조 현행화
### 다음 할 일
- v2 기획 및 태스크 정의
### 이슈/참고
- v1 전체 40개 태스크 (Phase 0~5) 완료
- 스킬/에이전트는 모두 범용적이므로 전부 유지
