import re


def _normalize_path(file_path: str, project_root: str, container_workdir: str) -> str | None:
    """traceback 파일 경로를 프로젝트 상대 경로로 정규화.

    로컬 개발: "backend/app/mail/services/gmail.py" → 그대로
    Docker:    "/app/app/mail/services/gmail.py"     → "backend/app/mail/services/gmail.py"
    """
    # Case 1: 이미 project_root가 포함됨 (로컬 개발 환경)
    if project_root in file_path:
        idx = file_path.find(project_root)
        return file_path[idx:]

    # Case 2: Docker 컨테이너 경로 → 프로젝트 상대 경로로 변환
    # project_root = "backend/app" → prefix = "backend/", module_dir = "app"
    parts = project_root.rstrip("/").split("/")
    if len(parts) < 2:
        return None
    prefix = "/".join(parts[:-1]) + "/"  # "backend/"
    module_dir = parts[-1]  # "app"

    # Docker WORKDIR 접두사 제거: /app/app/mail/... → app/mail/...
    stripped = file_path
    cwd = container_workdir.rstrip("/") + "/"
    if stripped.startswith(cwd):
        stripped = stripped[len(cwd):]

    # module_dir로 시작하는지 확인 (app/mail/... 형태)
    if stripped.startswith(module_dir + "/"):
        return prefix + stripped

    return None


def parse_stack_trace(
    stack_trace: str, project_root: str, container_workdir: str = "/app"
) -> list[dict]:
    """
    Python traceback에서 프로젝트 코드만 추출.

    로컬:   File "backend/app/mail/services/gmail.py", line 45, in sync_gmail
    Docker: File "/app/app/mail/services/gmail.py", line 45, in sync_gmail
    → [{"file": "backend/app/mail/services/gmail.py", "line": 45, "method": "sync_gmail"}]
    """
    pattern = r'File "([^"]+)", line (\d+), in (\w+)'
    matches = re.findall(pattern, stack_trace)

    results = []
    seen = set()
    for file_path, line, method in matches:
        relative_path = _normalize_path(file_path, project_root, container_workdir)
        if relative_path and relative_path not in seen:
            seen.add(relative_path)
            results.append({
                "file": relative_path,
                "line": int(line),
                "method": method,
            })
    return results


def extract_related_imports(
    source_code: str, project_root: str, already_fetched: set[str]
) -> list[str]:
    """
    Python 소스코드의 import문에서 프로젝트 내부 모듈 파일 경로를 추출.

    - 'from app.xxx import ...' 또는 'import app.xxx' 형태 파싱
    - project_root 기반으로 파일 경로 변환: app.mail.services.gmail → backend/app/mail/services/gmail.py
    - already_fetched에 있는 파일은 제외
    """
    # project_root에서 prefix 추출: "backend/app" → prefix="backend/", module_root="app"
    parts = project_root.rstrip("/").split("/")
    if len(parts) >= 2:
        prefix = "/".join(parts[:-1]) + "/"
        module_root = parts[-1]
    else:
        prefix = ""
        module_root = parts[0]

    # from app.xxx import ... 또는 import app.xxx 패턴
    from_pattern = rf"from\s+({re.escape(module_root)}(?:\.\w+)*)\s+import"
    import_pattern = rf"import\s+({re.escape(module_root)}(?:\.\w+)+)"

    modules = set()
    modules.update(re.findall(from_pattern, source_code))
    modules.update(re.findall(import_pattern, source_code))

    results = []
    for module in modules:
        # 모듈 경로를 파일 경로로 변환: app.mail.services.gmail → backend/app/mail/services/gmail.py
        file_path = prefix + module.replace(".", "/") + ".py"
        if file_path not in already_fetched:
            results.append(file_path)

    return list(dict.fromkeys(results))  # 순서 유지하면서 중복 제거
