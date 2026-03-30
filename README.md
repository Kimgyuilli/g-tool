# G-Tool 

메일, 캘린더, 할일, 북마크를 통합 관리하는 AI 기반 생산성 플랫폼.

<!-- 시연 영상 추가 예정 -->

## 주요 기능

- **메일 AI 분류** — Gmail, 네이버 메일을 Claude AI로 자동 분류 (업무/금융/쇼핑/뉴스레터 등)
- **Google Calendar 연동** — 일정 조회, 생성, 삭제를 통합 UI에서 관리
- **할일 칸반 보드** — Project > Task > Subtask 3단계 구조, 드래그앤드롭 칸반
- **북마크 관리** — 카테고리별 즐겨찾기 링크 저장 및 정리
- **500 에러 자동수정 봇** — 프로덕션 에러 발생 시 AI가 소스 분석 → 수정 PR 자동 생성

## 기술 스택

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Caddy](https://img.shields.io/badge/Caddy-1F88C0?logo=caddy&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude_API-Anthropic-d4a574)

| 영역 | 스택 |
|------|------|
| Backend | Python, FastAPI, SQLAlchemy (async), SQLite |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| AI | Claude API (메일 분류, 에러 분석) |
| 인증 | Google OAuth 2.0 + JWT 쿠키, 네이버 IMAP |
| 배포 | Docker Compose, Caddy (자동 HTTPS), Oracle Cloud ARM |
| CI/CD | GitHub Actions (lint + test → 자동 배포) |
| Error Bot | FastAPI, Claude API, GitHub API (자동 PR 생성) |

## 시스템 아키텍처

```
                         ┌─────────────────────────────────┐
                         │         Oracle Cloud ARM         │
                         │         (Docker Compose)         │
    ┌──────┐             │                                  │
    │Client│────HTTPS───▶│  Caddy (리버스 프록시 + TLS)     │
    └──────┘             │    │                             │
                         │    ├── /api/*  ──▶ Backend:8000  │
                         │    │               ├─ SQLite DB  │
                         │    │               ├─ Gmail API  │
                         │    │               ├─ Calendar   │
                         │    │               └─ Claude API │
                         │    │                             │
                         │    └── /*     ──▶ Frontend:3000  │
                         │                                  │
                         │  Error Bot:8001                  │
                         │    ├─ 500 에러 수신              │
                         │    ├─ Claude AI 분석             │
                         │    └─ GitHub PR 자동 생성        │
                         └─────────────────────────────────┘
```

## 프로젝트 구조

```
/
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── auth/         #   인증 (Google OAuth, JWT)
│   │   ├── mail/         #   메일 (Gmail, Naver, AI 분류)
│   │   ├── calendar/     #   Google Calendar 연동
│   │   ├── todo/         #   할일 (Project > Task > Subtask)
│   │   ├── bookmark/     #   북마크 관리
│   │   └── core/         #   공통 (DB, 의존성, 보안, 스케줄러)
│   └── tests/
├── frontend/             # Next.js 프론트엔드
│   └── src/
│       ├── app/          #   App Router 페이지
│       ├── features/     #   도메인별 컴포넌트/훅/타입
│       ├── components/   #   공통 UI (shadcn/ui)
│       └── __tests__/
├── bot/                  # Error Bot (500 에러 자동수정)
│   ├── app/
│   └── tests/
├── docker-compose.yml
├── Caddyfile
└── DEPLOY.md             # 배포 가이드
```

## 로컬 실행

### 사전 준비

- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 18+, [pnpm](https://pnpm.io/)
- Google OAuth 클라이언트 ID/Secret ([설정 가이드](references/guide-google-oauth-setup.md))
- Anthropic API 키

### Backend

```bash
cd backend
cp .env.example .env     # .env 편집하여 키 입력
uv sync
uv run fastapi dev app/main.py
```

`http://localhost:8000/docs`에서 API 문서 확인.

### Frontend

```bash
cd frontend
cp .env.example .env.local   # API URL 설정
pnpm install
pnpm dev
```

`http://localhost:3000`에서 앱 접속.

## 배포

Oracle Cloud Free Tier ARM VM에 Docker Compose로 배포합니다.
Caddy가 자동 HTTPS 인증서를 발급하고 리버스 프록시 역할을 합니다.

```bash
docker compose up -d --build
```

상세 배포 가이드: [DEPLOY.md](./DEPLOY.md)

## 프로젝트 규모

| 항목 | 수치 |
|------|------|
| 커밋 | 93개 |
| Backend (Python) | ~4,800줄 |
| Frontend (TS/TSX) | ~6,400줄 |
| Error Bot (Python) | ~1,700줄 |
| 테스트 파일 | 26개 (backend 10 + frontend 7 + bot 9) |

## 개발 과정

Phase별 작업 계획과 진행 기록은 아래 문서에서 확인할 수 있습니다.

- [PLAN.md](./PLAN.md) — v2 작업 계획 (Phase 6~22)
- [PROGRESS.md](./PROGRESS.md) — v2 진행 기록
- [PLAN_V1.md](./PLAN_V1.md) — v1 작업 계획 (Phase 0~5)
- [PROGRESS_V1.md](./PROGRESS_V1.md) — v1 진행 기록
