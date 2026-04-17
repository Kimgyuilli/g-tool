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

## Phase 23: 프로젝트 마무리 — README + 문서 정리

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| 루트 README.md 작성 | agent | done | — | 프로젝트 소개, 기능, 아키텍처, 실행법 |
| frontend/README.md 삭제 | agent | done | — | Next.js 기본 템플릿 제거 |
| PLAN/PROGRESS 아카이빙 | — | done | — | 현재 상태 유지 (개발 과정 증빙) |

## Phase 24: 세션 만료 개선

> JWT 만료 시간 연장 + 401 리다이렉트 + sliding session

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| JWT 만료 시간 24시간 → 7일 | agent | done | — | config.py |
| apiFetch 401 인터셉터 추가 | agent | done | — | api.ts, /auth/me 제외 |
| /auth/me sliding session | agent | done | — | 남은 시간 < 절반 시 토큰 갱신 |

## Phase 25: Google OAuth refresh 에러 방어선

> Calendar/Gmail API 호출 중 googleapiclient 내부에서 발생하는 `RefreshError`가 500으로 터지는 문제 해결. 선제 refresh 강화는 expiry 저장 컬럼 부재로 본 Phase 제외하고 별도 후속 이슈로 분리.
>
> 브랜치: `fix/google-refresh-error-handling`
>
> 핵심 결정 사항
> - 공통 모듈은 `backend/app/auth/google_errors.py`에 두고 router/worker 양쪽에서 재사용
> - 책임 3분할: `classify_google_refresh_error`(분류만) / `disconnect_google_account`(부수효과) / `build_google_refresh_http_exception`(HTTP 변환)
> - Enum `GoogleRefreshOutcome`: `TOKEN_INVALID_OR_EXPIRED` | `SCOPE_MISMATCH` (invalid_grant / 일반 만료 / 일시적 refresh 실패까지 포괄)
> - 선제 refresh 조건은 **변경 없음** — expiry 저장소 없는 상태에서 조건 확대하면 매 요청 refresh 유발

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| BE-1: auth/google_errors.py 신규 모듈 작성 | backend-dev | done | — | Enum + 3개 함수 분리 |
| BE-2: dependencies.py 공통 헬퍼 호출로 리팩토링 | backend-dev | done | BE-1 | 선제 refresh 조건 유지 |
| BE-3: background_sync.py 공통 헬퍼 사용 | backend-dev | done | BE-1 | worker 종료 정책(return 0) 유지 |
| BE-4: Calendar router 5개 엔드포인트 방어선 | backend-dev | done | BE-1 | calendars, events, event_detail, create, delete |
| BE-5: Gmail router 3개 엔드포인트 방어선 | backend-dev | done | BE-1 | sync, sync/full, apply-labels (messages 2개 제외) |
| BE-6: 라우터 회귀 테스트 추가 | backend-dev | done | BE-4, BE-5 | tests/routers/test_calendar.py 신규, test_gmail.py 확장 |
| BE-7: 기존 dependency 테스트 import 경로 조정 | backend-dev | done | BE-1 | monkeypatch 경로 변경 불필요 (import만 redirect) |
| BE-8: Lint + 전체 테스트 통과 확인 | backend-dev | done | 위 전체 | ruff clean, pytest 37 passed (무관 test_auth 2개 사전 failure) |

## Phase 26: Bot 실패 리포트 이슈화

> PR 생성 실패 시 Discord 알림만 오는 대신 GitHub Issue에 분석 리포트 자동 업로드. dedup + sanitize 적용.
>
> 브랜치: `phase26-bot-failure-issue-report`
>
> 핵심 결정 사항
> - Issue 생성 대상: pipeline 실패 경로 3~9 (AI 분석 이후). 1~2(스택/파일 조회 실패)는 Discord만
> - sanitize는 **선행 조건** — Bearer/Authorization/쿠키/이메일/`ya29.`/`1//` 토큰 패턴 마스킹 후 Issue/Discord 진입
> - sanitize 실패 시 제목은 `[hash] unknown_stage — pipeline internal error` 고정 포맷, 원본값 포함 금지
> - dedup: `sha256(errorType+errorMessage+stage)[:10]` → title prefix `[{dedup_key}]` + label `auto-fix-failed` + 24h 윈도우
> - dedup 조회: `repo.get_issues(state="open", labels=["auto-fix-failed"])` + 최근 50개 내 로컬 매칭. **50개 내 미발견 시 새 Issue 생성**
> - PyGithub version pin: `get_issues` 호환성 분기 코드가 지저분해지면 pin 우선

| 태스크 | 담당 | 상태 | 의존 | 비고 |
|--------|------|------|------|------|
| BOT-1: config 확장 | backend-dev | done | — | `issue_enabled`, `issue_labels`, `issue_dedup_window_hours` 추가 |
| BOT-2: sanitizer.py 신규 + 단위 테스트 | backend-dev | done | — | Bearer/Auth/Cookie/email/`ya29.`/`1//` 마스킹 + excerpt 유틸 |
| BOT-3: github_service.py 확장 | backend-dev | done | BOT-1 | `create_issue`, `find_open_issue_by_key`, `add_issue_comment` |
| BOT-4: issue_builder.py 신규 | backend-dev | done | BOT-2 | stage enum, dedup_key, sanitized payload만 허용 |
| BOT-5: discord_service.send_failure_alert 시그니처 확장 | backend-dev | done | — | `issue_url: str \| None` 인자 + Discord 필드 sanitize |
| BOT-6: pipeline.py report_failure 헬퍼로 통합 | backend-dev | done | BOT-3, BOT-4, BOT-5 | 실패 경로 3~8 통일, stage 1~2는 Discord only 유지 |
| BOT-7: pipeline L221 최상위 except 처리 | backend-dev | done | BOT-6 | `pipeline_internal_error` + sanitize fallback 제목 |
| BOT-8: 테스트 | backend-dev | done | BOT-6, BOT-7 | Issue 분기 + Discord sanitize 회귀 테스트 포함, `bot` 테스트 67 passed |
| BOT-9: 로컬 검증 + deploy.yml env 추가 여부 판단 | backend-dev | pending | BOT-8 | `/api/test-webhook` 수동 시나리오와 deploy env 반영 여부는 미진행 |

### Phase 26 구현 계획 구체화

> 현재 `bot/app/pipeline.py` 기준 실패 지점이 흩어져 있으므로, 먼저 "실패 리포트 데이터 계약"을 고정한 뒤 `pipeline.py`의 모든 후반부 실패 경로를 `report_failure(...)` 하나로 모은다. Stage 1~2(스택 파싱/파일 조회)는 Discord only, Stage 3~9(AI 분석 이후)는 Discord + GitHub Issue 대상으로 분리한다.

#### 26-1. 실패 단계(stage) 정의 고정

| stage | 현재 pipeline 위치 | Issue 생성 | 설명 |
|------|-------------------|-----------|------|
| `stack_trace_parse_failed` | entries 비어 있음 | no | 프로젝트 코드 위치를 못 찾은 경우 |
| `source_file_read_failed` | files 비어 있음 | no | 로컬 소스 읽기 실패 |
| `ai_analysis_failed` | `analyze_error()` 결과 없음 | yes | AI 응답 자체 없음 |
| `fix_skipped` | `should_fix == false` | yes | AI가 수정 불필요 판단 |
| `ai_validation_failed` | `validate_ai_result()` 실패 | yes | schema/known_files 검증 실패 |
| `diff_apply_failed` | `apply_changes()` 실패 | yes | original 블록 불일치 등 |
| `change_validation_failed` | `validate_changes()` 실패 | yes | 과도한 삭제 등 안전성 검증 실패 |
| `pull_request_failed` | `create_pull_request()` 예외 | yes | GitHub PR 생성 실패 |
| `pipeline_internal_error` | 최상위 `except` | yes | 위 stage 분류 밖 내부 예외 |

결정:
- `fix_skipped`도 운영 관점에서는 "자동 수정 파이프라인 결과"이므로 Issue 대상에 포함한다.
- `pipeline_internal_error`는 제목/본문 모두 sanitize fallback 허용 경로로 취급한다.
- dedup key 입력은 `error_type + error_message + stage` 고정, stack trace는 제외한다.

#### 26-2. 실패 리포트 데이터 계약

신규 `issue_builder.py`에서 아래 구조를 중심으로 조립한다.

| 필드 | 설명 |
|------|------|
| `stage` | 위 표의 stage enum 문자열 |
| `dedup_key` | `sha256(errorType + errorMessage + stage)[:10]` |
| `title` | `[{dedup_key}] {stage} - {short_error_type}` |
| `body` | sanitized summary, request URL, timestamp, sanitized reason, sanitized stack trace excerpt, 후속 액션 |
| `labels` | 기본 `auto-fix-failed` + 설정 라벨 |
| `issue_enabled` | config 플래그가 false면 GitHub 호출 없이 Discord만 전송 |

본문 원칙:
- 원문 stack trace/full reason을 그대로 싣지 않는다. sanitize 이후만 허용한다.
- 본문 길이는 GitHub Issue/Discord에서 모두 과도해지지 않게 excerpt 중심으로 제한한다.
- sanitize 실패 시 제목은 `[{dedup_key}] unknown_stage - pipeline internal error`로 다운그레이드한다.

#### 26-3. 파일별 구현 책임

| 파일 | 책임 |
|------|------|
| `bot/app/config.py` | Issue 관련 env 추가, 기본값/파싱 |
| `bot/app/services/sanitizer.py` | 민감정보 마스킹, 실패 안전 fallback |
| `bot/app/services/issue_builder.py` | stage enum, dedup key, title/body/labels 생성 |
| `bot/app/services/github_service.py` | Issue 조회/생성/댓글 추가 |
| `bot/app/services/discord_service.py` | failure alert에 `issue_url` 선택 인자 추가 |
| `bot/app/pipeline.py` | `report_failure()` 도입, Stage 3~9 공통화 |
| `bot/tests/*` | sanitizer, issue builder, pipeline, discord/github service 회귀 테스트 |

#### 26-4. 구현 순서

1. `config.py` 확장
2. `sanitizer.py`와 테스트 작성
3. `issue_builder.py`에서 stage enum + payload 생성 로직 작성
4. `github_service.py`에 Issue CRUD helper 추가
5. `discord_service.py`에 `issue_url` 필드 연동
6. `pipeline.py`에 `report_failure(report, stage, reason, *, issue_payload=None)` 헬퍼 도입
7. 기존 Stage 3~8 실패 분기를 모두 `report_failure()`로 치환
8. 최상위 `except`에서 sanitize fallback + `pipeline_internal_error` 처리
9. 전체 테스트 및 `/api/test-webhook` 검증

이 순서를 고정하는 이유:
- sanitize/data contract가 먼저 고정돼야 Discord/GitHub/pipeline이 같은 포맷을 공유할 수 있다.
- `pipeline.py`를 먼저 건드리면 실패 경로가 늘어나고 테스트 기준점이 흔들린다.

#### 26-5. GitHub Issue 동작 정책

생성 정책:
- `issue_enabled=false`면 Issue 생성/조회/댓글 추가를 모두 건너뛴다.
- `issue_enabled=true`이고 stage가 Issue 대상이면 open issue 최근 50개 내에서 dedup key를 찾는다.
- 찾으면 새 Issue 대신 comment 추가 후 기존 URL 반환.
- 못 찾으면 새 Issue 생성.

댓글 정책:
- comment는 "재발생 시점 + sanitized reason 요약"만 추가한다.
- 동일 실행 내에서 중복 comment 방지를 위해 `report_failure()` 호출은 각 실패 경로당 1회만 허용한다.

레이블 정책:
- 기본 라벨은 `auto-fix-failed`.
- 추가 라벨은 env에서 comma-separated로 받아 trim 후 병합한다.

PyGithub 정책:
- 우선 현재 버전 API 범위 내에서 `repo.get_issues(state="open", labels=[...])` 사용.
- 구현 중 labels 인자 호환 분기 코드가 과도해지면 버전 pin을 별도 커밋으로 분리해 처리한다.

#### 26-6. sanitize 규칙

최소 마스킹 대상:
- `Authorization: Bearer ...`
- `Bearer ...`
- `Cookie: ...`
- 이메일 주소
- Google OAuth access token 패턴 (`ya29.`)
- Google refresh token 계열 패턴 (`1//`)

출력 원칙:
- 길이를 유지할 필요는 없고 식별 불가능성이 우선이다.
- 값 전체를 보존하지 말고 `[REDACTED_TOKEN]`, `[REDACTED_EMAIL]` 같은 토큰으로 치환한다.
- sanitize 함수는 예외를 던지지 않고, 내부 실패 시 안전한 축약 문자열을 반환한다.

#### 26-7. 테스트 매트릭스

필수 테스트:
- `sanitizer.py`: Bearer/Auth/Cookie/email/`ya29.`/`1//` 마스킹
- `issue_builder.py`: stage별 title/body/dedup_key 생성, fallback 제목 검증
- `github_service.py`: 기존 open issue 발견 시 comment 경로, 미발견 시 create 경로
- `discord_service.py`: `issue_url is None` / 존재 둘 다 embed 생성 검증
- `pipeline.py`:
  - AI 결과 없음 → `ai_analysis_failed`
  - `should_fix=false` → `fix_skipped`
  - validation 실패 → `ai_validation_failed`
  - diff 적용 실패 → `diff_apply_failed`
  - change validation 실패 → `change_validation_failed`
  - PR 생성 예외 → `pull_request_failed`
  - 최상위 except → `pipeline_internal_error`
  - stage 1~2는 Issue 생성 안 함

검증 포인트:
- Discord로 전달되는 `reason`도 sanitize 결과만 사용되는지 확인
- dedup key가 동일하면 create 대신 comment로 분기하는지 확인
- sanitize 실패 fallback 시 원본 민감정보가 제목/본문에 남지 않는지 확인

#### 26-8. 배포/운영 체크리스트

- 신규 env 후보:
  - `ISSUE_ENABLED=true`
  - `ISSUE_LABELS=auto-fix-failed`
  - `ISSUE_DEDUP_WINDOW_HOURS=24`
- `deploy.yml` 수정은 config 구현 후 실제 신규 env가 확정될 때만 반영
- `/api/test-webhook` 검증 시나리오:
  - 정상 Discord 발송
  - GitHub Issue 생성 enabled 시 issue 생성 또는 기존 issue comment
  - 민감정보 포함 메시지 입력 시 sanitize 결과 확인

#### 26-9. 완료 조건(Definition of Done)

- Stage 3~9 실패 경로가 모두 `report_failure()`로 통합되어 중복 로직이 제거됨
- Discord failure alert에 선택적으로 Issue URL이 포함됨
- 민감정보가 Discord/GitHub 어디에도 원문으로 남지 않음
- dedup으로 같은 실패가 24시간 내 새 Issue를 무한 생성하지 않음
- 관련 테스트 통과 및 로컬 수동 시나리오 1회 확인

## 후속 이슈 (별도 PR)

- **User 모델에 `google_token_expiry` 컬럼 추가 + 선제 refresh 활성화**
  - 마이그레이션 필요 (스키마 변경)
  - `exchange_code` / refresh 성공 시 `credentials.expiry` 저장
  - `dependencies.py`에서 `credentials.expired` 기반 선제 refresh 활성화 가능
  - Phase 25가 머지된 뒤에 별도 이슈로 진행
