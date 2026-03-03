# 진행 기록

> v1 (Phase 0~5) 기록 아카이브: [PROGRESS_V1.md](./PROGRESS_V1.md)

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
