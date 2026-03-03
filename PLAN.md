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
