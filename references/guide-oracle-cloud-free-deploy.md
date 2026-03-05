---
title: Oracle Cloud Free Tier FastAPI + Next.js 배포 가이드
tags: [deployment, oracle-cloud, free-tier, docker, nginx, https]
created: 2026-03-02
updated: 2026-03-02
status: draft
---

# Oracle Cloud Free Tier FastAPI + Next.js 배포 가이드

> **주의**: 이 문서는 2025년 1월까지의 정보를 기반으로 작성되었습니다. 실제 배포 전 Oracle Cloud 공식 문서에서 최신 스펙과 정책을 확인하세요.

## 1. Oracle Cloud Always Free Tier 스펙

### 1.1 Compute (ARM Ampere A1)

**무료 제공 리소스:**
- **4 OCPUs** (ARM Ampere A1 vCPU)
- **24 GB RAM**
- 최대 4개의 VM 인스턴스로 분할 가능 (예: 1x4 OCPU, 2x2 OCPU, 4x1 OCPU 등)
- 권장: **1개 VM에 4 OCPU + 24 GB RAM 할당** (G-Tool 배포용)

**스토리지:**
- 부트 볼륨: 최대 **200 GB** (총합)
- 블록 볼륨: 최대 **200 GB** (총합)
- 권장: 부트 볼륨 100 GB (OS + Docker + 로그), 블록 볼륨 50 GB (DB 백업)

### 1.2 네트워크

**무료 제공:**
- **고정 퍼블릭 IP 2개** (Reserved Public IP)
- 아웃바운드 데이터 전송: **월 10 TB**
- 인바운드 데이터 전송: **무제한**
- Load Balancer: Always Free에는 미포함 (Flexible Load Balancer는 유료)

**포트 설정:**
- 기본적으로 SSH(22)만 열려있음
- HTTP(80), HTTPS(443) 포트는 Security List/NSG에서 수동으로 열어야 함

### 1.3 계정 생성 시 주의사항

**필수 요구사항:**
- 신용카드 또는 PayPal 계정 (인증 목적, 실제 청구 없음)
- 전화번호 인증 (SMS)
- 이메일 인증

**중요 팁:**
- **Home Region 선택이 중요**: 한번 선택하면 변경 불가 (서울, 춘천, 도쿄, 오사카 등 선택 가능)
- **Compartment 사용**: Root가 아닌 별도 Compartment에서 리소스 관리 권장
- **신용카드 검증 실패 시**: Oracle 지원팀에 문의 (일부 카드사에서 해외 결제 차단)

### 1.4 Always Free 인스턴스 회수(Reclaim) 방지

**회수되는 케이스:**
1. **Idle 인스턴스** (7일 이상 CPU 사용률 < 10%)
2. **90일 이상 미로그인 계정**
3. **계정 정지** (약관 위반, 신용카드 만료 등)

**방지법:**
- **Cron Job**: 5분마다 간단한 작업 실행 (예: `*/5 * * * * echo "keep-alive" >> /var/log/keepalive.log`)
- **모니터링**: Oracle Cloud Monitoring (무료)로 CPU 사용률 확인
- **정기 로그인**: 최소 월 1회 콘솔 로그인
- **카드 정보 유지**: 신용카드 만료일 갱신

---

## 2. 배포 아키텍처

### 2.1 단일 VM 구성 (Docker Compose)

```
┌─────────────────────────────────────────────────────────┐
│ Oracle Cloud VM (Ampere A1, 4 OCPU, 24 GB RAM)         │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Caddy (Reverse Proxy + HTTPS)                    │    │
│  │ :80, :443                                         │    │
│  └──────────┬─────────────────┬────────────────────┘    │
│             │                 │                          │
│  ┌──────────▼──────┐ ┌────────▼─────────┐               │
│  │ Next.js (FE)    │ │ FastAPI (BE)     │               │
│  │ :3000           │ │ :8000            │               │
│  └─────────────────┘ └────────┬─────────┘               │
│                               │                          │
│                      ┌────────▼─────────┐               │
│                      │ SQLite (DB)      │               │
│                      │ /data/mail.db    │               │
│                      └──────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Docker Compose 예시

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/<username>/g-tool-backend:latest
    container_name: g-tool-backend
    restart: unless-stopped
    volumes:
      - ./data:/app/data  # SQLite DB
      - ./backend/.env:/app/.env:ro
    environment:
      - DATABASE_URL=sqlite:///./data/mail.db
    ports:
      - "127.0.0.1:8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: ghcr.io/<username>/g-tool-frontend:latest
    container_name: g-tool-frontend
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_URL=https://yourdomain.com/api
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - backend

  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend

volumes:
  caddy_data:
  caddy_config:
```

### 2.3 Caddyfile (자동 HTTPS)

```caddyfile
yourdomain.com {
    # 프론트엔드 (Next.js)
    reverse_proxy frontend:3000

    # 백엔드 API
    handle /api/* {
        reverse_proxy backend:8000
    }

    # 로그
    log {
        output file /var/log/caddy/access.log
    }

    # HTTPS 자동 인증서 (Let's Encrypt)
    tls {
        email your-email@example.com
    }
}
```

**Caddy vs Nginx:**
- **Caddy**: HTTPS 자동 설정, 설정 간단 (권장)
- **Nginx**: 더 많은 커스터마이징 가능, Certbot 필요

---

## 3. 도메인 및 네트워킹

### 3.1 무료 도메인 옵션

1. **Freenom** (`.tk`, `.ml`, `.ga` 등)
   - 무료이지만 신뢰도 낮음, Google OAuth에서 차단될 수 있음
   - 비추천

2. **DuckDNS** (서브도메인)
   - `yourname.duckdns.org` 형식
   - 무료, HTTPS 지원 (Let's Encrypt)
   - Oracle Cloud 고정 IP와 연결 가능
   - **권장**: 개인 프로젝트용

3. **Cloudflare Pages/Workers** (서브도메인)
   - `yourproject.pages.dev` 형식
   - 프론트엔드만 호스팅 가능 (백엔드는 Oracle Cloud)
   - HTTPS 기본 지원

4. **유료 도메인** (`.com`, `.net` 등)
   - Namecheap, Cloudflare Registrar (연 $8~15)
   - 프로덕션 배포 시 권장

### 3.2 Oracle Cloud 고정 IP 할당

**Always Free 범위 내:**
- Reserved Public IP **2개 무료**
- 인스턴스에 할당한 IP는 인스턴스 재시작 후에도 유지됨

**할당 방법:**
```bash
# OCI 콘솔에서
Networking > IP Management > Reserved Public IPs > Reserve Public IP Address

# 또는 OCI CLI
oci network public-ip create \
  --compartment-id <compartment-ocid> \
  --lifetime RESERVED \
  --display-name g-tool-ip
```

**도메인 연결:**
- DNS A 레코드에 고정 IP 설정
- 예: `yourdomain.com` → `123.45.67.89`

---

## 4. OAuth 관련 설정

### 4.1 Google OAuth 리다이렉트 URI 변경

**현재 (로컬):**
```
http://localhost:8000/auth/google/callback
```

**배포 후 (퍼블릭 도메인):**
```
https://yourdomain.com/api/auth/google/callback
```

**변경 방법:**
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. APIs & Services > Credentials
3. OAuth 2.0 클라이언트 ID 선택
4. "Authorized redirect URIs"에 추가:
   - `https://yourdomain.com/api/auth/google/callback`
   - `https://www.yourdomain.com/api/auth/google/callback` (www 서브도메인도 추가 권장)

**프론트엔드 환경변수 (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
```

**백엔드 환경변수 (`backend/.env`):**
```bash
FRONTEND_URL=https://yourdomain.com
REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
```

### 4.2 CORS 설정

**FastAPI CORS (`backend/app/main.py`):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발용
        "https://yourdomain.com",  # 프로덕션
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 5. 실전 배포 단계

### 5.1 VM 생성

```bash
# OCI CLI 사용 (또는 콘솔에서 수동 생성)
oci compute instance launch \
  --availability-domain <AD-name> \
  --compartment-id <compartment-ocid> \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
  --image-id <ubuntu-22.04-aarch64-image-ocid> \
  --subnet-id <subnet-ocid> \
  --assign-public-ip true \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
  --display-name g-tool-vm
```

**권장 OS:**
- Ubuntu 22.04 LTS (ARM64)
- Oracle Linux 8 (ARM64)

### 5.2 보안 그룹 설정

**Ingress Rules (인바운드):**
| 프로토콜 | 소스 | 포트 | 용도 |
|---------|------|------|------|
| TCP | 0.0.0.0/0 | 22 | SSH (본인 IP로 제한 권장) |
| TCP | 0.0.0.0/0 | 80 | HTTP (HTTPS로 리다이렉트) |
| TCP | 0.0.0.0/0 | 443 | HTTPS |
| ICMP | 0.0.0.0/0 | - | Ping (선택) |

**UFW 방화벽 (Ubuntu):**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5.3 SSH 접속 및 초기 설정

```bash
# SSH 접속
ssh -i ~/.ssh/id_rsa ubuntu@<public-ip>

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose 설치
sudo apt install docker-compose-plugin -y

# Git 설치 (선택)
sudo apt install git -y
```

### 5.4 프로젝트 배포

```bash
# 프로젝트 클론 또는 파일 전송
git clone https://github.com/<username>/g-tool.git
cd g-tool

# 환경변수 설정
nano backend/.env
# (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CLAUDE_API_KEY 등 설정)

nano frontend/.env.local
# NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Docker Compose 실행
docker compose up -d

# 로그 확인
docker compose logs -f
```

### 5.5 도메인 연결 및 HTTPS 활성화

```bash
# DuckDNS 예시
curl "https://www.duckdns.org/update?domains=yourname&token=<your-token>&ip=<public-ip>"

# Caddyfile 수정
nano Caddyfile
# yourdomain.duckdns.org { ... }

# Caddy 재시작
docker compose restart caddy

# HTTPS 인증서 자동 발급 확인
docker compose logs caddy | grep -i certificate
```

---

## 6. 백업 및 유지보수

### 6.1 SQLite 백업

**Cron Job (`/etc/cron.daily/backup-db`):**
```bash
#!/bin/bash
DB_PATH=/home/ubuntu/g-tool/data/mail.db
BACKUP_DIR=/home/ubuntu/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 로컬 백업
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/mail_$DATE.db'"

# 오래된 백업 삭제 (30일 이상)
find $BACKUP_DIR -name "mail_*.db" -mtime +30 -delete

# (선택) Oracle Object Storage로 업로드
# oci os object put --bucket-name backups --file $BACKUP_DIR/mail_$DATE.db
```

**실행 권한:**
```bash
sudo chmod +x /etc/cron.daily/backup-db
```

### 6.2 로그 로테이션

```bash
# Docker 로그 크기 제한 (docker-compose.yml)
version: '3.8'
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 6.3 모니터링

**Oracle Cloud Monitoring (무료):**
- CPU, 메모리, 네트워크 사용량 추적
- Alarm 설정 (CPU > 90% 지속 시 이메일 알림)

**Docker 헬스체크:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## 7. 비용 관련 주의사항

### 7.1 Always Free 범위 내 유지

**무료 리소스 한도:**
- Ampere A1: 4 OCPU, 24 GB RAM (총합)
- 부트 볼륨: 200 GB (총합)
- 블록 볼륨: 200 GB (총합)
- 아웃바운드 데이터: 월 10 TB

**유료 전환되는 케이스:**
- Load Balancer 사용 (유료)
- x86 VM 사용 (Always Free는 ARM만)
- 스토리지 200 GB 초과
- 아웃바운드 데이터 10 TB 초과

### 7.2 예산 알람 설정

```bash
# OCI 콘솔에서
Billing & Cost Management > Budgets > Create Budget

# 예산: $0.50 (Always Free 초과 시 알림)
# Alert: 50%, 100% 사용 시 이메일 발송
```

---

## 8. 문제 해결

### 8.1 VM 생성 실패 ("Out of host capacity")

**원인:**
- 특정 Availability Domain에서 Ampere A1 리소스 부족

**해결:**
1. 다른 AD 시도
2. 다른 Home Region 선택 (서울 → 춘천, 도쿄 등)
3. 새벽 시간대(KST 2~6시) 재시도
4. OCI CLI 스크립트로 자동 재시도:
   ```bash
   while ! oci compute instance launch ...; do sleep 60; done
   ```

### 8.2 포트 80/443 접속 불가

**체크리스트:**
1. Security List에서 Ingress Rule 확인
2. UFW 방화벽 설정 확인 (`sudo ufw status`)
3. iptables 확인 (`sudo iptables -L`)
4. Oracle Linux의 경우 `firewalld` 확인
5. Docker 네트워크 모드 확인 (`host` vs `bridge`)

### 8.3 HTTPS 인증서 발급 실패

**원인:**
- 도메인 DNS 설정 미완료 (A 레코드)
- 포트 80/443 차단
- Caddy 로그 확인 필요

**해결:**
```bash
# DNS 전파 확인
nslookup yourdomain.com

# Caddy 상세 로그
docker compose logs caddy

# 수동 인증서 발급 (Certbot)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

---

## 9. 추가 최적화

### 9.1 CDN (Cloudflare)

**무료 CDN + DDoS 보호:**
1. Cloudflare 계정 생성
2. 도메인 추가 (네임서버 변경)
3. SSL/TLS 설정: Full (strict)
4. Caching 설정: 정적 파일 캐싱

**장점:**
- Oracle Cloud 아웃바운드 데이터 절약
- 글로벌 CDN으로 속도 개선
- HTTPS 자동 활성화

### 9.2 Swap 설정 (메모리 부족 시)

```bash
# 4 GB Swap 생성
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 9.3 Docker 이미지 최적화

**Multi-stage Build (Dockerfile):**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 10. 참고 자료

- [Oracle Cloud Always Free Tier 공식 문서](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [Caddy 공식 문서](https://caddyserver.com/docs/)
- [DuckDNS 가이드](https://www.duckdns.org/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Next.js 프로덕션 체크리스트](https://nextjs.org/docs/going-to-production)

---

## TODO

- [ ] 실제 Oracle Cloud 계정 생성 후 스크린샷 추가
- [ ] Terraform 스크립트 작성 (IaC)
- [ ] CI/CD 파이프라인 구성 (GitHub Actions → OCI)
- [ ] PostgreSQL 마이그레이션 (SQLite → PostgreSQL on OCI)
- [ ] 모니터링 대시보드 (Grafana + Prometheus)
- [ ] 2026년 3월 기준 최신 정보 업데이트 필요 (WebSearch 활성화 시)

---

**작성일**: 2026-03-02
**작성자**: researcher agent
**소스**: 2025년 1월까지의 지식 기반 (최신 정보는 Oracle 공식 문서 참조 필요)
