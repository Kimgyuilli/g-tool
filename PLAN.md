# 작업 계획

> v1 (Phase 0~5) 완료 — 아카이브: [PLAN_V1.md](./PLAN_V1.md)

## Phase 6: Oracle Cloud 배포

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 환경변수 기반 설정 전환 | backend-dev | done | — | config.py, main.py, auth.py |
| Next.js standalone 빌드 설정 | frontend-dev | done | — | next.config.ts |
| Backend Dockerfile 작성 | backend-dev | done | — | Python 3.13-slim + uv |
| Frontend Dockerfile 작성 | frontend-dev | done | — | Multi-stage, standalone |
| Docker Compose + Caddy 설정 | backend-dev | done | — | 리버스 프록시 + 자동 HTTPS |
| .dockerignore + env 템플릿 | backend-dev | done | — | |
| Oracle VM 프로비저닝 + 배포 | — | done | 위 전체 | A1.Flex, Reserved IP, gtool.kro.kr |

## Phase 7: CI/CD

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| CI/CD 파이프라인 설계 | agent | done | — | GitHub Actions |
| CI: 린트 + 테스트 워크플로우 | agent | done | — | backend ruff/pytest, frontend eslint/vitest/build |
| CD: 자동 배포 워크플로우 | agent | done | CI | workflow_run → SSH → docker compose |
| ~~gh-aw ci-doctor~~ | — | 취소 | — | Copilot Pro 필요, 추후 재검토 |
| ~~gh-aw pr-fix~~ | — | 취소 | — | Copilot Pro 필요, 추후 재검토 |

## Phase 8: HTML 이메일 렌더링

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| DB body_html 컬럼 추가 | backend-dev | done | — | Mail 모델에 Text nullable 컬럼 |
| Gmail/Naver _extract_body → text+html 추출 | backend-dev | done | — | dict 반환 방식으로 변경 |
| API 응답에 body_html 포함 | backend-dev | done | — | helpers.py |
| DOMPurify 기반 HtmlEmailRenderer 컴포넌트 | frontend-dev | done | — | whitelist 방식 XSS 방지 |
| MailDetailView 조건부 렌더링 | frontend-dev | done | — | html 있으면 HTML, 없으면 plain text |
| Tailwind Typography 플러그인 | frontend-dev | done | — | @tailwindcss/typography |
| sync_gmail_messages body_html 누락 수정 | backend-dev | done | — | 단일 페이지 sync 함수 버그 |

## Phase 9: Google Calendar 통합

> 플랫폼을 종합 생산성 도구로 확장하는 첫 단계. Google Calendar를 연동하여 일정을 조회/관리할 수 있도록 한다.

### 9-1. 백엔드 — OAuth 스코프 확장 + Calendar API

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| OAuth 스코프에 calendar.readonly 추가 | backend-dev | done | — | google_auth.py SCOPES에 추가 |
| Calendar Service 구현 | backend-dev | done | 스코프 확장 | calendar_service.py — list_calendars, list_events, get_event |
| Calendar API 라우터 구현 | backend-dev | done | Calendar Service | routers/calendar.py — /calendars, /events, /events/{id} |
| 재인증 플로우 처리 | backend-dev | done | 스코프 확장 | prompt="consent" 기존 설정이 자동 처리, 기존 사용자 로그아웃→재로그인 필요 |

### 9-2. 프론트엔드 — 앱 네비게이션 구조 변경

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 앱 네비게이션 추가 (메일/캘린더 탭) | frontend-dev | done | — | AppHeader에 페이지 전환 UI 추가 완료 |
| 라우팅 구조 변경 | frontend-dev | done | 네비게이션 | page.tsx에 activePage 상태 추가, 조건부 렌더링 |

### 9-3. 프론트엔드 — Calendar UI

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Calendar 타입 정의 | frontend-dev | done | — | types/calendar.ts 생성 완료 |
| useCalendar 훅 구현 | frontend-dev | done | Calendar 타입, API 라우터 | hooks/useCalendar.ts 생성 완료 |
| 월간 캘린더 뷰 컴포넌트 | frontend-dev | done | useCalendar | CalendarMonthView.tsx — 월간 그리드, 이벤트 표시 완료 |
| 이벤트 상세 패널 | frontend-dev | done | 월간 뷰 | CalendarEventDetail.tsx — 이벤트 클릭 시 상세 정보 완료 |
| 캘린더 목록 사이드바 | frontend-dev | done | useCalendar | CalendarSidebar.tsx — 캘린더별 필터링 완료 |
| 통합 캘린더 뷰 | frontend-dev | done | 위 전체 | CalendarView.tsx — 레이아웃 통합, page.tsx 연동 완료 |
| 이벤트 생성 기능 | frontend-dev | done | 통합 캘린더 뷰 | EventCreateModal.tsx, useCalendar createEvent 추가 |
| 주간/일간 캘린더 뷰 컴포넌트 | frontend-dev | pending | 월간 뷰 | CalendarWeekView.tsx — 타임라인 기반 주간/일간 뷰 (추후 구현) |

### 의존 관계 요약

```
9-1 OAuth 스코프 확장
 ├→ 9-1 Calendar Service → 9-1 API 라우터 ─┐
 └→ 9-1 재인증 플로우                        │
                                             ├→ 9-3 useCalendar → 9-3 월간 뷰 → 9-3 주간/일간 뷰
9-2 네비게이션 → 9-2 라우팅 ─────────────────┘                                 → 9-3 이벤트 상세
                                                                               → 9-3 캘린더 사이드바
9-3 Calendar 타입 (독립)
```

### 9-4. 백엔드 — Calendar 쓰기 권한 + 이벤트 생성

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| OAuth 스코프 calendar.events로 변경 | backend-dev | done | 9-3 이벤트 생성 기능 | calendar.readonly → calendar.events, OAUTHLIB_RELAX_TOKEN_SCOPE 설정 |
| Calendar Service에 create_event 추가 | backend-dev | done | 스코프 변경 | calendar_service.py — create_event 구현 |
| POST /events API 구현 | backend-dev | done | Calendar Service | routers/calendar.py — POST /events |

### 기술 결정 사항

- **Calendar 라이브러리**: 직접 구현 vs 라이브러리 (FullCalendar 등) — 태스크 진행 시 결정
- **데이터 캐싱**: 초기엔 DB 저장 없이 실시간 API 호출, 필요 시 캐싱 추가
- **스코프**: `calendar.readonly`로 시작 (읽기 전용), 이벤트 생성/수정은 추후 확장 → **9-4에서 쓰기 권한 확장**
- **google-api-python-client 이미 설치됨** — Calendar API v3 바로 사용 가능

## Phase 10: DDD 도메인 패키지 분리

> 백엔드를 DDD 기반 도메인 패키지(core/, auth/, mail/, calendar/)로, 프론트엔드를 feature 폴더(features/mail/, features/calendar/, features/auth/)로 재구성

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Phase A: Backend core/auth/calendar 패키지 생성 | agent | done | — | core/, auth/, calendar/ |
| Phase B: Backend mail 도메인 + main.py 업데이트 | agent | done | Phase A | mail/, background_sync, shim 제거 |
| Phase C: Frontend feature 폴더 구조 | agent | done | — | features/mail/, calendar/, auth/ |
| 검증: lint + 테스트 + 빌드 | agent | done | Phase A,B,C | ruff, pytest 24/24, pnpm lint+build 통과 |

## Phase 11: TodoList 기능 추가

> 메일+캘린더+할일 통합 생산성 도구로 확장. 자체 DB에 저장하는 Project > Task > Subtask 3단계 구조.

### 11-1. Backend — 모델 + CRUD API

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Todo models.py (Project, Task, Subtask) | backend-dev | done | — | SQLAlchemy Mapped[] 스타일 |
| Todo schemas.py | backend-dev | done | — | Pydantic 요청/응답 모델 |
| Todo service.py | backend-dev | done | models | async CRUD + 소유권 검증 |
| Todo router.py + main.py 등록 | backend-dev | done | service, schemas | /api/todo prefix |

### 11-2. Frontend — 타입 + 훅 + 기본 UI

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Todo types.ts | frontend-dev | done | — | Project, Task, Subtask 인터페이스 |
| useTodo + useSubtasks 훅 | frontend-dev | done | types, 11-1 | apiFetch 패턴 |
| ProjectSidebar 컴포넌트 | frontend-dev | done | types | 프로젝트 목록 + 생성 |
| TaskListView 컴포넌트 | frontend-dev | done | types | 퀵 추가, 체크박스, 우선순위 |
| TaskDetailView 컴포넌트 | frontend-dev | done | types, useSubtasks | 서브태스크 목록 |
| TodoPage 통합 | frontend-dev | done | 위 전체 | 3-panel 레이아웃 |
| page.tsx + AppHeader 연동 | frontend-dev | done | TodoPage | nav에 할일 탭 추가 |
