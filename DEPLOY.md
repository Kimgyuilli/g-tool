# Oracle Cloud Free Tier 배포 가이드

G-Tool를 Oracle Cloud ARM VM에 Docker Compose로 배포하는 단계별 가이드.

---

## 사전 준비물

- [ ] Oracle Cloud 계정 (신용카드 인증 완료)
- [ ] 도메인 1개 (유료 도메인 또는 DuckDNS 무료 서브도메인)
- [ ] Google OAuth 클라이언트 ID/Secret (이미 있음)
- [ ] Anthropic API 키 (이미 있음)

---

## Step 1: Oracle Cloud VM 생성

### 1-1. 콘솔 접속
https://cloud.oracle.com → 로그인 → Compute > Instances > Create Instance

### 1-2. 인스턴스 설정
| 항목 | 값 |
|------|-----|
| Name | `g-tool` |
| Image | **Ubuntu 22.04** (Canonical, aarch64) |
| Shape | **VM.Standard.A1.Flex** |
| OCPU | **4** (최대 무료) |
| Memory | **24 GB** (최대 무료) |
| Boot volume | 50 GB (기본값, 충분) |

### 1-3. 네트워크 설정
- VCN: 기본 생성 또는 기존 VCN 사용
- **Public IPv4 address**: Assign a public IPv4 address 체크
- **SSH key**: 로컬 PC의 `~/.ssh/id_rsa.pub` 내용 붙여넣기

> SSH 키가 없으면: `ssh-keygen -t ed25519` 로 생성

### 1-4. "Out of host capacity" 에러 발생 시
ARM 인스턴스는 수요가 높아서 생성 실패할 수 있음.
- 다른 Availability Domain 선택
- 새벽 시간대(KST 2~6시) 재시도
- OCPU를 2~3으로 줄여서 시도 후, 나중에 늘리기

---

## Step 2: 보안 규칙 (포트 열기)

VM 생성 후, **Security List**에서 HTTP/HTTPS 포트를 열어야 함.

### OCI 콘솔에서:
1. Networking > Virtual Cloud Networks > VCN 선택
2. Subnets > Public Subnet 선택
3. Security Lists > Default Security List 선택
4. **Add Ingress Rules**:

| Source CIDR | Protocol | Dest Port | 설명 |
|-------------|----------|-----------|------|
| `0.0.0.0/0` | TCP | 80 | HTTP |
| `0.0.0.0/0` | TCP | 443 | HTTPS |

(SSH 22번은 기본으로 열려 있음)

---

## Step 3: VM 초기 설정

### 3-1. SSH 접속
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<VM의 Public IP>
```

### 3-2. 시스템 업데이트 + Docker 설치
```bash
# 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 로그아웃 후 재접속 (docker 그룹 적용)
exit
ssh -i ~/.ssh/id_rsa ubuntu@<IP>

# 확인
docker --version
docker compose version
```

### 3-3. OS 방화벽 열기 (iptables)
Oracle Linux / Ubuntu에서 OS 레벨 방화벽도 열어줘야 함:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

> `netfilter-persistent`가 없으면: `sudo apt install iptables-persistent -y`

---

## Step 4: 도메인 설정

### 옵션 A: DuckDNS (무료, 권장)
1. https://www.duckdns.org 접속, GitHub/Google 로그인
2. 서브도메인 생성 (예: `my-g-tool`)
3. IP에 VM의 Public IP 입력 → Update
4. 결과: `my-g-tool.duckdns.org`

### 옵션 B: 유료 도메인
- DNS A 레코드에 VM의 Public IP 설정
- 예: `mail.mydomain.com` → `<VM Public IP>`

---

## Step 5: 프로젝트 배포

### 5-1. 코드 가져오기
```bash
git clone https://github.com/<username>/g-tool.git
cd g-tool
```

> 프라이빗 리포인 경우: SSH key를 VM에 설정하거나, Personal Access Token 사용

### 5-2. 환경변수 설정

**`.env.production`** (docker-compose용 도메인 설정):
```bash
cp .env.production.example .env.production
nano .env.production
```
```env
DOMAIN=my-g-tool.duckdns.org    # ← 실제 도메인으로 변경
```

**`backend/.env`** (API 키 설정):
```bash
cp backend/.env.example backend/.env
nano backend/.env
```
```env
ANTHROPIC_API_KEY=sk-ant-api03-실제키
GOOGLE_CLIENT_ID=실제-클라이언트-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-실제-시크릿
GOOGLE_REDIRECT_URI=https://my-g-tool.duckdns.org/api/auth/callback
FRONTEND_URL=https://my-g-tool.duckdns.org
```

### 5-3. 빌드 & 실행
```bash
# .env.production 로드하여 docker compose 실행
docker compose --env-file .env.production up -d --build
```

초회 빌드는 ARM에서 5~10분 소요될 수 있음.

### 5-4. 상태 확인
```bash
# 컨테이너 상태
docker compose --env-file .env.production ps

# 로그 확인
docker compose --env-file .env.production logs -f

# 개별 서비스 로그
docker compose --env-file .env.production logs backend
docker compose --env-file .env.production logs caddy
```

---

## Step 6: Google OAuth 리다이렉트 URI 추가

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. APIs & Services > Credentials
3. OAuth 2.0 클라이언트 ID 선택
4. **Authorized redirect URIs**에 추가:
   ```
   https://my-g-tool.duckdns.org/api/auth/callback
   ```
5. **Authorized JavaScript origins**에 추가:
   ```
   https://my-g-tool.duckdns.org
   ```
6. 저장

---

## Step 7: 접속 확인

브라우저에서:
```
https://my-g-tool.duckdns.org
```

- Caddy가 자동으로 Let's Encrypt HTTPS 인증서를 발급함 (1~2분 소요)
- 첫 접속 시 잠시 기다리면 됨

### 확인 체크리스트
- [ ] HTTPS 접속 가능 (자물쇠 아이콘)
- [ ] 프론트엔드 화면 표시
- [ ] Google 로그인 → OAuth 콜백 정상 작동
- [ ] 메일 목록 조회 가능
- [ ] AI 분류 작동

---

## 유지보수

### 코드 업데이트
```bash
cd ~/g-tool
git pull
docker compose --env-file .env.production up -d --build
```

### 재시작
```bash
docker compose --env-file .env.production restart
```

### 중지
```bash
docker compose --env-file .env.production down
```

### DB 백업
```bash
# Docker 볼륨에서 SQLite 파일 복사
docker cp $(docker compose --env-file .env.production ps -q backend):/app/data/gtool.db ./backup_$(date +%Y%m%d).db
```

### Idle 인스턴스 회수 방지
Oracle은 7일 이상 CPU < 10%인 VM을 회수할 수 있음. 메일 자동 동기화 스케줄러가 돌고 있으므로 보통 문제없지만, 추가 안전장치:

```bash
# crontab에 추가 (5분마다 keep-alive)
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -s http://localhost:8000/health > /dev/null") | crontab -
```

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| 사이트 접속 안 됨 | Security List 미설정 | Step 2 확인 |
| 사이트 접속 안 됨 | OS 방화벽 차단 | Step 3-3 iptables 확인 |
| HTTPS 안 됨 | 도메인 DNS 미전파 | `nslookup 도메인` 확인, 5~10분 대기 |
| HTTPS 안 됨 | 포트 80 차단 | Caddy는 80번으로 인증서 발급 (필수 개방) |
| OAuth 실패 | Redirect URI 불일치 | Step 6에서 정확한 URI 등록 확인 |
| 502 Bad Gateway | 백엔드 미시작 | `docker compose logs backend` 확인 |
| 빌드 실패 (메모리) | RAM 부족 | Swap 추가: 아래 참고 |

### Swap 추가 (빌드 시 메모리 부족할 경우)
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
