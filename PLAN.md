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
| ~~주간/일간 캘린더 뷰 컴포넌트~~ | frontend-dev | 취소 | 월간 뷰 | 불필요하여 취소 |

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

## Phase 12: Todo 칸반 보드 리팩토링

> Project 계층 제거 → Task + Subtask 2단계 플랫 구조. 3열 칸반 보드 UI + @dnd-kit 드래그앤드롭.

### 12-1. Backend — 모델/API 단순화

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Project 모델 삭제, Task에 user_id 추가 | backend-dev | done | — | models.py |
| Project 스키마 삭제 | backend-dev | done | — | schemas.py |
| Project 서비스 삭제, Task/Subtask 직접 검증 | backend-dev | done | — | service.py |
| Project 엔드포인트 삭제, GET /tasks 추가 | backend-dev | done | — | router.py |

### 12-2. Frontend — 칸반 보드 UI

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| types.ts 리팩토링 (Project 제거, status 변경) | frontend-dev | done | — | TaskStatus 타입 추가 |
| useTodo 훅 리팩토링 (플랫 조회) | frontend-dev | done | — | GET /tasks |
| KanbanBoard 컴포넌트 | frontend-dev | done | — | @dnd-kit, 3열 칸반 |
| KanbanCard 컴포넌트 | frontend-dev | done | — | 드래그, 인라인 확장 |
| TodoPage 리팩토링 | frontend-dev | done | — | KanbanBoard만 렌더링 |
| 구 컴포넌트 삭제 | frontend-dev | done | — | ProjectSidebar, TaskListView, TaskDetailView |
| 검증: ruff + lint + build | agent | done | — | 모두 통과 |

## Phase 13: Todo 코드 최적화 및 개선

> 백엔드/프론트엔드 코드 품질, 타입 안전성, 성능, UX 개선

### 13-1. Backend — 타입 안전성 + 성능

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| schemas.py: status/priority Literal 검증 | backend-dev | done | — | str → Literal 제한 |
| schemas.py: ReorderRequest 타입 안전화 | backend-dev | done | — | list[dict] → list[ReorderItem] |
| service.py: reorder N+1 쿼리 개선 | backend-dev | done | — | 일괄 조회 후 업데이트 |
| service.py: update_task subtask 이중 로드 제거 | backend-dev | done | — | 최초 조회에 selectinload 포함 |
| service.py: Pydantic response model 도입 | backend-dev | done | — | _to_dict → Pydantic 모델 |
| schemas.py: due_date 파싱 schema 레벨로 이동 | backend-dev | done | — | validator로 datetime 변환 |

### 13-2. Frontend — 낙관적 업데이트 + UX

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| useTodo: CUD 낙관적 업데이트 | frontend-dev | done | — | re-fetch 제거, 로컬 상태 업데이트 |
| useTodo: 에러 시 데이터 보존 | frontend-dev | done | — | setTasks([]) → 기존 유지 |
| KanbanBoard: handleDragEnd 로직 단순화 | frontend-dev | done | — | 이중 처리 제거 |
| KanbanCard: descDraft 동기화 | frontend-dev | done | — | useEffect 또는 key 활용 |
| TodoPage: prop drilling 개선 | frontend-dev | done | — | Context 도입 |
| KanbanCard: 컨텍스트 메뉴 open 제어 | frontend-dev | done | — | dispatchEvent → Radix open/onOpenChange |

## Phase 14: 북마크 (즐겨찾기 링크) 기능 추가

> 자주 사용하는 웹사이트를 한 곳에 모아두는 북마크 페이지. 카테고리별 분류 지원.

### 14-1. Backend — 모델 + CRUD API

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Bookmark 모델 (BookmarkCategory, Bookmark) | backend-dev | done | — | models.py |
| Bookmark 스키마 | backend-dev | done | — | schemas.py |
| Bookmark 서비스 | backend-dev | done | models | service.py |
| Bookmark 라우터 + main.py 등록 | backend-dev | done | service | /api/bookmark prefix |

### 14-2. Frontend — 타입 + 훅 + UI

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Bookmark types.ts | frontend-dev | done | — | 인터페이스 + 색상 상수 |
| useBookmarks 훅 | frontend-dev | done | types, 14-1 | 카테고리+북마크 CRUD |
| BookmarkCard/Grid/Sidebar 컴포넌트 | frontend-dev | done | types | UI 컴포넌트 |
| AddBookmarkModal/AddCategoryModal | frontend-dev | done | types | Dialog 컴포넌트 |
| BookmarkContext + BookmarkPage | frontend-dev | done | 위 전체 | Provider + 레이아웃 |
| page.tsx + AppHeader 연동 | frontend-dev | done | BookmarkPage | nav에 북마크 탭 추가 |

## Phase 15: 캘린더 동기화(새로고침) 버튼 추가

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| CalendarSidebar에 RefreshCw 버튼 추가 | frontend-dev | done | — | onRefresh, refreshing props |
| CalendarPage에 handleRefresh 로직 추가 | frontend-dev | done | — | loadCalendars + loadEvents + toast |

## Phase 16: 캘린더 일정 삭제 기능 추가

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Backend: delete_event 서비스 함수 | backend-dev | done | — | service.py |
| Backend: DELETE /events/{event_id} 엔드포인트 | backend-dev | done | — | router.py |
| Frontend: useCalendar deleteEvent 함수 | frontend-dev | done | — | useCalendar.ts |
| Frontend: CalendarEventDetail 삭제 버튼 | frontend-dev | done | — | CalendarEventDetail.tsx |
| Frontend: CalendarPage deleteEvent 연동 | frontend-dev | done | — | CalendarPage.tsx |

## Phase 17: 프로젝트 리네이밍 (Mail Organizer → G-Tool)

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 코드 내 프로젝트명/설명 변경 | agent | done | — | pyproject.toml, main.py, exceptions.py, layout.tsx, AppHeader, LoginScreen |
| 테스트 코드 업데이트 | agent | done | — | smoke.test.tsx, LoginScreen.test.tsx |
| 에이전트 설명 업데이트 | agent | done | — | .claude/agents/ 5개 파일 |
| 문서 업데이트 | agent | done | — | CLAUDE.md, DEPLOY.md, references/ |
| DB 파일명 변경 | agent | done | — | config.py, docker-compose.yml |
| deploy.yml 서버 경로 변경 | agent | done | — | cd ~/g-tool |
| 메모리 파일 업데이트 | agent | done | — | MEMORY.md |
| GitHub 레포 rename + 배포 서버 폴더/DB rename | — | done | PR 병합 후 | 수동 완료 |

## Phase 18: 메일 분류 시스템 최적화

> OpenAI gpt-4o-mini 분류 시스템의 토큰 효율, 처리 속도, 사용자 피드백 개선

### 18-1. 토큰 최적화 + JSON 안정성

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| Structured Outputs 적용 + _extract_json 제거 | backend-dev | done | — | response_format json_schema |
| 본문 truncate 500→300자, 청크 10→15개 | backend-dev | done | — | classifier.py |
| SYSTEM_PROMPT JSON 지시 제거 | backend-dev | done | — | Structured Outputs가 보장 |

### 18-2. 병렬 처리

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| asyncio.gather + Semaphore(3) 병렬 처리 | backend-dev | done | 18-1 | classifier.py |

### 18-3. SSE 실시간 진행 피드백

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| classify_batch에 on_progress 콜백 | backend-dev | done | 18-2 | classifier.py |
| POST /api/classify/mails SSE 변경 | backend-dev | done | on_progress | classify.py |
| 프론트엔드 fetch streaming + 진행률 UI | frontend-dev | done | SSE 엔드포인트 | useMailActions, AppHeader, page.tsx |

## Phase 19: 500 Error Auto-Fix Bot

> 프로덕션 500 에러 발생 시 Discord 알림 + AI 분석 + 자동 수정 PR 생성. 기존 500-pr-bot을 Python/FastAPI 환경에 맞게 이식.

### 19-1. error-bot 코드 이식 (bot/ 디렉토리)

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| bot/ 디렉토리 복사 + 불필요 파일 제거 | agent | done | — | static/, admin.py, errors.py, test_runner.py 제거 |
| stack_trace_parser.py Python traceback 파서로 재작성 | agent | done | T1 | Java → Python 파서 |
| ai_service.py 프롬프트 수정 | agent | done | T1 | Spring Boot → FastAPI+Next.js |
| config.py 환경변수 수정 | agent | done | T1 | base_package → project_root |
| pipeline.py 수정 | agent | done | T2,T4 | 파서 호출부 변경 |
| .env.example 업데이트 | agent | done | T4 | G-Tool 환경변수 |

### 19-2. G-Tool 백엔드 — 500 에러 리포터 미들웨어

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| error_reporter.py 미들웨어 생성 | agent | done | — | 500 에러 → error-bot POST |
| main.py + config.py 미들웨어 등록 | agent | done | T7 | error_bot_url 설정 |

### 19-3. Docker Compose + 배포 설정

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| docker-compose.yml error-bot 서비스 추가 | agent | done | 19-1 | 내부 통신 전용 |

### 19-4. 테스트 + 검증

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 테스트 수정 + lint 검증 | agent | done | 19-1,19-2 | 58 passed, ruff clean |

## Phase 20: 환경변수 관리 개선 — GitHub Secrets 기반

> backend/.env, bot/.env, .env.production을 서버에서 수동 관리하는 대신, GitHub Secrets에서 deploy 시 자동 생성

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| deploy.yml에서 GitHub Secrets로 .env 파일 자동 생성 | agent | done | — | backend/.env, bot/.env, .env.production |

## Phase 21: Error-Bot AI 분석 품질 개선

> PR #14에서 드러난 문제 해결: AI가 파일 전체 재작성, gpt-4o-mini 코드 추론 부족, 불필요한 수정, 검증 로직 부재

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 모델 gpt-4o-mini → gpt-4o, max_tokens 증가 | agent | done | — | ai_provider.py |
| 프롬프트/스키마 전면 개편 (diff 기반 + should_fix) | agent | done | — | ai_service.py |
| diff 적용 로직 + 검증 강화 | agent | done | 스키마 | pipeline.py |
| PR builder changes 형식 지원 | agent | done | 스키마 | pr_builder.py |
| 테스트 업데이트 | agent | done | 위 전체 | test_ai_service, test_pipeline |
| 검증: lint + 테스트 | agent | done | 테스트 | ruff + pytest 52 passed |

## Phase 22: 보안 개선 — [PR #19](https://github.com/Kimgyuilli/g-tool/pull/19)

> URL query parameter `user_id`를 JWT 쿠키 인증으로 교체, DB 토큰 암호화, Caddy 보안 헤더, error-bot 볼륨 마운트 축소

### 22-1. 인프라 보안

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 볼륨 마운트 축소 (error-bot) | agent | done | — | docker-compose.yml |
| Caddy 보안 헤더 추가 | agent | done | — | Caddyfile |

### 22-2. JWT 세션 인증

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| PyJWT 의존성 + config 설정 | agent | done | — | pyproject.toml, config.py |
| JWT 유틸리티 (security.py) | agent | done | — | create/verify access token |
| get_current_user → Cookie JWT | agent | done | security.py | core/dependencies.py |
| OAuth callback → 쿠키 설정 + logout | agent | done | security.py | auth/router.py |
| 프론트엔드 credentials: include | agent | done | — | api.ts |
| useAuth 쿠키 기반으로 전면 단순화 | agent | done | — | useAuth.ts |
| 모든 훅에서 user_id query 제거 | agent | done | — | 10개 파일 ~35곳 |
| deploy.yml SECRET_KEY 추가 | agent | done | — | deploy.yml |

### 22-3. DB 토큰 암호화

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| cryptography 의존성 + Fernet 유틸리티 | agent | done | — | pyproject.toml, security.py |
| 토큰 저장/읽기 지점 암호화 적용 | agent | done | Fernet | auth, naver, background_sync |
| 마이그레이션 스크립트 | agent | done | Fernet | migrate_encrypt.py |
