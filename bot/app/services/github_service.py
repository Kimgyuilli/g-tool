import logging
from datetime import UTC, datetime, timedelta

from github import Github, GithubException, InputGitTreeElement
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)

_repo = None


def _get_repo():
    global _repo
    if _repo is None:
        github = Github(settings.github_token)
        _repo = github.get_repo(settings.github_repo)
    return _repo


def health_check() -> dict:
    """GitHub API 연결 상태 확인."""
    try:
        repo = _get_repo()
        _ = repo.full_name
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def _issue_has_dedup_key(issue, dedup_key: str) -> bool:
    return issue.title.startswith(f"[{dedup_key}]")


def find_open_issue_by_key(dedup_key: str, labels: list[str]):
    repo = _get_repo()
    cutoff = datetime.now(UTC) - timedelta(hours=settings.issue_dedup_window_hours)
    issues = repo.get_issues(state="open", labels=labels)
    checked = 0

    for issue in issues:
        checked += 1
        if checked > 50:
            break
        created_at = getattr(issue, "created_at", None)
        if created_at and created_at.replace(tzinfo=UTC) < cutoff:
            continue
        if _issue_has_dedup_key(issue, dedup_key):
            return issue
    return None


def create_issue(title: str, body: str, labels: list[str]) -> str:
    repo = _get_repo()
    issue = repo.create_issue(title=title, body=body, labels=labels)
    return issue.html_url


def add_issue_comment(issue, body: str) -> str:
    issue.create_comment(body)
    return issue.html_url


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
def create_pull_request(
    files: list[dict],
    summary: str,
    pr_body: str,
    branch_name: str,
) -> str:
    """브랜치 생성 → atomic 커밋 (Git Tree API) → PR 생성. PR URL 반환."""
    repo = _get_repo()
    base_branch = settings.github_base_branch

    # 1. base 브랜치의 최신 SHA
    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    base_sha = base_ref.object.sha

    # 2. 새 브랜치 생성 (이미 존재하면 재사용)
    try:
        repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)
    except GithubException as e:
        if e.status == 422:  # already exists
            logger.warning("브랜치 이미 존재, 재사용: %s", branch_name)
        else:
            raise

    # 3. Git Tree API로 atomic 커밋 (파일 수와 무관하게 1회 커밋)
    tree_elements = [
        InputGitTreeElement(
            path=f["path"], mode="100644", type="blob", content=f["content"]
        )
        for f in files
    ]
    base_tree = repo.get_git_tree(base_sha)
    new_tree = repo.create_git_tree(tree_elements, base_tree)

    parent_commit = repo.get_git_commit(base_sha)
    new_commit = repo.create_git_commit(
        f"fix: {summary}", new_tree, [parent_commit]
    )

    branch_ref = repo.get_git_ref(f"heads/{branch_name}")
    branch_ref.edit(new_commit.sha)

    # 4. PR 생성
    pr = repo.create_pull(
        title=f"fix: {summary}",
        body=pr_body,
        head=branch_name,
        base=base_branch,
    )
    return pr.html_url
