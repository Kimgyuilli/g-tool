# Mail Organizer

Gmail과 네이버 메일을 통합 관리하고, AI 기반으로 자동 분류하는 플랫폼.

## 에이전트 워크플로우

> **새 세션을 시작하면 반드시 `PLAN.md`와 `PROGRESS.md`를 먼저 읽고 현재 상황을 파악한 뒤 작업을 시작한다.**

### PLAN.md — 작업 계획
- 현재 진행 중인 Phase와 남은 태스크 목록을 관리한다.
- 각 태스크는 담당자(에이전트), 상태, 의존 관계를 명시한다.
- 새로운 태스크가 생기면 PLAN.md에 추가하고, 완료/변경 시 즉시 업데이트한다.
- 형식:
  ```
  ## Phase N: 제목
  | 태스크 | 담당 | 상태 | 의존 | 비고 |
  |--------|------|------|------|------|
  | 태스크 설명 | agent-id | pending/in-progress/done/blocked | 선행 태스크 | 메모 |
  ```

### PROGRESS.md — 진행 기록
- 각 에이전트가 작업을 시작/완료할 때마다 기록한다.
- 최신 항목이 위로 오도록 역순으로 작성한다.
- 다음 에이전트가 읽었을 때 "지금 어디까지 됐고, 무엇을 해야 하는지" 즉시 파악할 수 있어야 한다.
- 형식:
  ```
  ## YYYY-MM-DD HH:MM — agent-id
  ### 완료한 작업
  - 작업 내용 (관련 파일 경로 포함)
  ### 다음 할 일
  - 다음 에이전트가 이어서 해야 할 작업
  ### 이슈/참고
  - 발견된 문제, 결정 사항, 주의점
  ```

### 에이전트 작업 규칙
1. **시작**: `/sync`로 컨텍스트 파악 (또는 수동으로 PLAN.md → PROGRESS.md 읽기)
2. **레퍼런스 확인**: 태스크에 관련된 기존 조사 자료가 있는지 `/ref`로 검색
3. **태스크 선택**: `/next`로 다음 수행 가능한 태스크 확인
4. **작업 중**: PLAN.md 해당 태스크 상태를 `in-progress`로 변경
5. **완료 시**: `/done <태스크명>`으로 완료 처리
6. **블로커 발생 시**: `/blocked <태스크명> <이유>`로 블로커 기록
7. **조사 완료 시**: 새로 알게 된 기술 정보는 `/save-ref`로 반드시 저장
8. **전체 워크플로우**: `/implement-task`로 선택→구현→검증→기록까지 한번에 수행

### 사용 가능한 스킬 (`.claude/skills/`)

| 스킬 | 용도 | 예시 |
|------|------|------|
| `/sync` | 현재 프로젝트 상황 요약 | `/sync` |
| `/next` | 다음 수행 가능한 태스크 제안 | `/next` |
| `/done` | 태스크 완료 처리 + 기록 | `/done OAuth 인증 구현` |
| `/blocked` | 태스크 블로커 기록 | `/blocked OAuth 인증 API 키 미발급` |
| `/review` | 코드 리뷰 (보안, 버그, 컨벤션) | `/review` 또는 `/review backend/app/services/gmail_service.py` |
| `/test` | 테스트 실행 + 결과 요약 | `/test backend` 또는 `/test all` |
| `/setup-check` | 개발 환경 점검 | `/setup-check` |
| `/implement-task` | 태스크 풀 워크플로우 | `/implement-task Gmail API 연동` |
| `/branch` | feature 브랜치 + worktree 생성 | `/branch feat/gmail-batch-sync` |
| `/pr` | PR 생성 | `/pr` |
| `/ref` | 레퍼런스 검색/조회 | `/ref gmail oauth`, `/ref --tag api`, `/ref --list` |
| `/save-ref` | 조사 결과를 레퍼런스로 저장 | `/save-ref api-gmail Gmail API 조사 결과` |

### 서브에이전트 (`.claude/agents/`)

태스크를 전문 에이전트에게 위임하여 병렬 작업이 가능하다.

| 에이전트 | 역할 | 사용 가능한 스킬 | 병렬 가능 |
|----------|------|-----------------|-----------|
| **planner** | 계획 수립, 태스크 분해/할당, PLAN.md 관리 | sync, next, done, blocked, ref | - |
| **backend-dev** | FastAPI 백엔드 구현 | ref, done, blocked, review, test | frontend-dev와 병렬 |
| **frontend-dev** | Next.js 프론트엔드 구현 | ref, done, blocked, review, test | backend-dev와 병렬 |
| **researcher** | 기술 조사, references/ 저장 | ref, save-ref | 다른 에이전트와 병렬 |
| **reviewer** | 코드 리뷰 (읽기 전용) | ref, review | - |

#### 병렬 실행 패턴

```
# 패턴 1: 조사 + 구현 병렬
researcher(Gmail API 조사) ─┐
                            ├→ backend-dev(API 구현)
기존 코드 탐색 ─────────────┘

# 패턴 2: 백엔드 + 프론트엔드 병렬
backend-dev(API 엔드포인트) ──┬→ reviewer(리뷰) → planner(기록)
frontend-dev(UI 컴포넌트) ────┘

# 패턴 3: 풀 파이프라인 (/implement-task)
planner(계획) → researcher(조사) → backend-dev + frontend-dev(구현) → reviewer(리뷰) → planner(기록)
```

## Git 워크플로우 (GitHub Flow + Worktree)

- **main** 브랜치는 항상 배포 가능한 상태를 유지한다.
- 모든 작업은 feature 브랜치에서 진행하고 PR로 병합한다.
- git worktree를 사용하여 브랜치별 독립 디렉토리에서 작업한다.
- worktree 기본 경로: `C:/Users/rlarb/coding/.worktrees/`

### 브랜치 네이밍
- `feat/<설명>` — 새 기능
- `fix/<설명>` — 버그 수정
- `refactor/<설명>` — 리팩토링
- `docs/<설명>` — 문서

### 작업 플로우
1. `/branch feat/기능명` → 브랜치 + worktree 생성
2. worktree 디렉토리에서 작업
3. 커밋 + push
4. `/pr` → PR 생성
5. 리뷰 후 main에 병합

## 프로젝트 목표

1. Gmail API를 통해 메일을 가져오고, AI(Claude API)로 내용 기반 자동 라벨 분류
2. 네이버 메일을 IMAP으로 연동하여 동일한 분류 체계 적용
3. 통합 UI에서 Gmail + 네이버 메일을 한 화면에서 조회, 분류, 정리
4. 백그라운드 자동화 (주기적 메일 체크 → 자동 분류)

## 기술 스택

- **Backend**: Python (FastAPI)
- **Frontend**: Next.js (React, App Router)
- **Database**: SQLite (개발) → PostgreSQL (배포)
- **AI**: Claude API (메일 분류, 요약)
- **인증**: Google OAuth 2.0, 네이버 IMAP 인증
- **패키지 관리**: Backend - uv / Frontend - pnpm

## 프로젝트 구조

```
/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py             # FastAPI 엔트리포인트
│   │   ├── config.py           # 환경 설정
│   │   ├── core/               # 공통 인프라
│   │   │   ├── database.py     # Base, engine, get_db, AsyncSessionLocal
│   │   │   ├── dependencies.py # get_current_user
│   │   │   ├── exceptions.py   # 커스텀 예외 클래스
│   │   │   └── background_sync.py # 스케줄러 (교차 도메인 orchestrator)
│   │   ├── auth/               # 인증 도메인
│   │   │   ├── router.py       # /auth 라우터
│   │   │   ├── service.py      # Google OAuth (create_auth_url, build_credentials 등)
│   │   │   └── dependencies.py # get_google_user, get_naver_user
│   │   ├── mail/               # 메일 도메인
│   │   │   ├── models.py       # User, Mail, Label, Classification, SyncState
│   │   │   ├── routers/        # gmail.py, naver.py, inbox.py, classify.py
│   │   │   └── services/       # gmail.py, naver.py, classifier.py, feedback.py, helpers.py
│   │   ├── calendar/           # 캘린더 도메인
│   │   │   ├── router.py       # /api/calendar 라우터
│   │   │   ├── service.py      # Google Calendar API
│   │   │   └── schemas.py      # CreateEventRequest
│   │   ├── todo/               # 할일 도메인
│   │   │   ├── models.py       # Task, Subtask
│   │   │   ├── schemas.py      # Pydantic 요청 모델
│   │   │   ├── service.py      # async CRUD + 소유권 검증
│   │   │   └── router.py       # /api/todo 라우터
│   │   └── bookmark/           # 북마크 도메인
│   │       ├── models.py       # BookmarkCategory, Bookmark
│   │       ├── schemas.py      # Pydantic 요청 모델
│   │       ├── service.py      # async CRUD + 소유권 검증
│   │       └── router.py       # /api/bookmark 라우터
│   ├── tests/                  # pytest 테스트
│   ├── pyproject.toml
│   └── .env                    # 시크릿 (git 미추적)
├── frontend/                   # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/                # App Router 페이지
│   │   ├── features/           # 도메인별 feature 폴더
│   │   │   ├── mail/           # 메일 feature
│   │   │   │   ├── components/ # MailListView, MailDetailView, CategorySidebar 등
│   │   │   │   ├── hooks/      # useMessages, useMailActions, useCategoryCounts 등
│   │   │   │   ├── types.ts    # MailMessage, MailDetail, CategoryCountsResponse 등
│   │   │   │   └── constants.ts # CATEGORY_COLORS, CATEGORY_DOT_COLORS
│   │   │   ├── bookmark/       # 북마크 feature
│   │   │   │   ├── BookmarkContext.tsx
│   │   │   │   ├── BookmarkPage.tsx
│   │   │   │   ├── components/ # BookmarkCard, BookmarkGrid, BookmarkCategorySidebar 등
│   │   │   │   ├── hooks/      # useBookmarks
│   │   │   │   └── types.ts    # Bookmark, BookmarkCategory
│   │   │   ├── calendar/       # 캘린더 feature
│   │   │   │   ├── CalendarPage.tsx
│   │   │   │   ├── components/ # CalendarMonthView, CalendarEventDetail 등
│   │   │   │   ├── hooks/      # useCalendar
│   │   │   │   └── types.ts    # CalendarEvent, CalendarInfo 등
│   │   │   ├── todo/           # 할일 feature
│   │   │   │   ├── TodoPage.tsx
│   │   │   │   ├── components/ # ProjectSidebar, TaskListView, TaskDetailView
│   │   │   │   ├── hooks/      # useTodo, useSubtasks
│   │   │   │   └── types.ts    # Project, Task, Subtask
│   │   │   └── auth/           # 인증 feature
│   │   │       ├── components/ # LoginScreen, NaverConnectModal
│   │   │       ├── hooks/      # useAuth, useNaverConnect
│   │   │       └── types.ts    # UserInfo
│   │   ├── components/         # 공통 컴포넌트
│   │   │   ├── ui/             # shadcn/ui (Button, Badge, Dialog 등)
│   │   │   ├── AppHeader.tsx   # 앱 헤더 (페이지 전환, 액션 버튼)
│   │   │   └── Pagination.tsx  # 범용 페이지네이션
│   │   ├── lib/                # API 클라이언트, 유틸
│   │   ├── utils/              # 유틸 함수
│   │   └── __tests__/          # vitest 테스트
│   ├── package.json
│   └── .env.local              # 프론트 환경변수 (git 미추적)
├── references/                 # 조사 자료
│   ├── README.md               # 레퍼런스 형식/규칙
│   └── guide-google-oauth-setup.md
├── CLAUDE.md
├── PLAN.md                     # 작업 계획 (v2~)
├── PLAN_V1.md                  # v1 작업 계획 아카이브
├── PROGRESS.md                 # 진행 기록 (v2~)
├── PROGRESS_V1.md              # v1 진행 기록 아카이브
└── .gitignore
```

## 구현 로드맵

### v1 (완료) — 상세: [PLAN_V1.md](./PLAN_V1.md)
- [x] **Phase 1**: Gmail 연동 + AI 분류 (MVP) — OAuth, Gmail API, Claude 분류, 라벨 적용, 기본 UI
- [x] **Phase 2**: 네이버 메일 연동 — IMAP, 통합 DB 스키마, 동일 AI 분류
- [x] **Phase 3**: 통합 UI + 자동화 — 통합 인박스, 사이드바, DnD, 스케줄러, 피드백 학습
- [x] **Phase 4**: 코드 모듈화/리팩토링 — 헬퍼, Depends, 예외, 컴포넌트/훅 분리, 테스트
- [x] **Phase 5**: UI 디자인 리뉴얼 — shadcn/ui, 3-panel 레이아웃, 반응형, 다크모드

### v2 — 상세: [PLAN.md](./PLAN.md)
- [x] **Phase 6**: Oracle Cloud 배포
- [x] **Phase 7**: CI/CD
- [x] **Phase 8**: HTML 이메일 렌더링
- [x] **Phase 9**: Google Calendar 통합
- [x] **Phase 10**: DDD 도메인 패키지 분리
- [x] **Phase 11**: TodoList 기능 (Project > Task > Subtask 3단계)
- [x] **Phase 12**: Todo 칸반 보드 리팩토링
- [x] **Phase 13**: Todo 코드 최적화 및 개선
- [x] **Phase 14**: 북마크 (즐겨찾기 링크) 기능

## 개발 컨벤션

- 커밋 메시지: 한글 허용, Conventional Commits 형식 (`feat:`, `fix:`, `docs:` 등)
- Backend: Python 3.12+, 타입 힌트 필수, ruff로 린트
- Frontend: TypeScript strict mode, ESLint + Prettier
- API 응답: JSON, snake_case 키
- 환경변수: `.env` 파일 사용, 시크릿은 절대 커밋하지 않음

## 주요 API/서비스 설정 참고

### Gmail API
- Google Cloud Console → Gmail API 활성화
- OAuth 2.0 클라이언트 ID 생성 (웹 애플리케이션)
- 스코프: `gmail.readonly`, `gmail.labels`, `gmail.modify`

### 네이버 메일 IMAP
- 네이버 메일 설정 → POP3/IMAP 사용 설정
- IMAP 서버: `imap.naver.com:993` (SSL)
- 네이버 앱 비밀번호 또는 OAuth (네이버 개발자센터)

### Claude API
- Anthropic Console에서 API 키 발급
- 모델: claude-sonnet-4-5-20250929 (비용 효율)
- 메일 분류 프롬프트는 `backend/app/services/classifier.py`에서 관리

## 명령어

```bash
# Backend
cd backend && uv run fastapi dev app/main.py

# Frontend
cd frontend && pnpm dev

# Lint
cd backend && uv run ruff check .
cd frontend && pnpm lint
```
