---
title: Google Cloud OAuth 2.0 셋업 가이드
tags: [google, oauth, gmail, api, setup]
created: 2026-02-26
updated: 2026-02-26
status: reviewed
---

# Google Cloud OAuth 2.0 셋업 가이드

## Step 1: Google Cloud 프로젝트 생성

1. https://console.cloud.google.com/ 접속
2. 상단 프로젝트 선택 드롭다운 → **새 프로젝트**
3. 프로젝트 이름: `G-Tool` (또는 원하는 이름)
4. **만들기** 클릭
5. 1~2분 대기

## Step 2: Gmail API 활성화

1. 좌측 메뉴 → **API 및 서비스** → **라이브러리**
2. `Gmail API` 검색 → 클릭
3. **사용** 버튼 클릭

직접 링크: https://console.cloud.google.com/apis/library/gmail.googleapis.com

## Step 3: OAuth 동의 화면 설정

URL: https://console.cloud.google.com/apis/credentials/consent

### 3a. 사용자 유형 선택
- **외부** 선택 (개인 계정용) → **만들기**

### 3b. 앱 정보 입력
- **앱 이름**: G-Tool
- **사용자 지원 이메일**: 본인 이메일
- **개발자 연락처 이메일**: 본인 이메일
- 나머지는 건너뛰기 가능 → **저장 후 계속**

### 3c. 스코프 추가
- **범위 추가 또는 삭제** 클릭
- 다음 3개 검색/선택:

| 스코프 | 용도 |
|--------|------|
| `https://www.googleapis.com/auth/gmail.readonly` | 메일 읽기 |
| `https://www.googleapis.com/auth/gmail.labels` | 라벨 관리 |
| `https://www.googleapis.com/auth/gmail.modify` | 메일 수정 (라벨 적용) |

- **업데이트** → **저장 후 계속**

### 3d. 테스트 사용자 추가
- **사용자 추가** → 본인 Gmail 주소 입력
- **저장 후 계속**

## Step 4: OAuth 2.0 클라이언트 ID 생성

URL: https://console.cloud.google.com/apis/credentials

1. **사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
2. **애플리케이션 유형**: 웹 애플리케이션
3. **이름**: G-Tool Backend
4. **승인된 리디렉션 URI** → URI 추가:
   ```
   http://localhost:8000/auth/callback
   ```
5. **만들기** 클릭

## Step 5: 크리덴셜 다운로드

1. 생성된 클라이언트 ID 우측의 **⬇️ 다운로드** 아이콘 클릭
2. `client_secret_xxx.json` 파일 다운로드됨
3. `backend/credentials.json`으로 이름 변경하여 저장

## Step 6: .env 파일 작성

`backend/.env`:
```
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

## 주의사항

| 항목 | 내용 |
|------|------|
| **테스트 모드 토큰 만료** | 외부 + 테스트 모드에서는 refresh token이 7일 후 만료 |
| **테스트 사용자 제한** | 테스트 모드에서는 등록한 사용자만 로그인 가능 (최대 100명) |
| **credentials.json 보안** | `.gitignore`에 반드시 포함, 분실 시 재생성 필요 |
| **localhost는 HTTP 허용** | 로컬 개발에서는 HTTPS 불필요, 배포 시에는 HTTPS 필수 |
| **refresh token 100개 제한** | 사용자당 100개 초과 시 오래된 토큰 자동 무효화 |

## 참고 링크

- https://developers.google.com/workspace/guides/create-project
- https://developers.google.com/workspace/guides/create-credentials
- https://developers.google.com/workspace/guides/configure-oauth-consent
- https://developers.google.com/workspace/gmail/api/auth/scopes
