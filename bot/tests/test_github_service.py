from unittest.mock import MagicMock, patch

from github import GithubException

from app.services.github_service import create_pull_request, fetch_file_content, fetch_files
from app.config import settings


# --- 로컬 파일 조회 ---


def test_fetch_file_content_returns_decoded(tmp_path):
    (tmp_path / "backend/app").mkdir(parents=True)
    target = tmp_path / "backend/app/main.py"
    target.write_text("from fastapi import FastAPI", encoding="utf-8")

    settings.local_source_path = str(tmp_path)
    try:
        result = fetch_file_content("backend/app/main.py")
        assert result == "from fastapi import FastAPI"
    finally:
        settings.local_source_path = ""


def test_fetch_file_content_returns_none_on_error(tmp_path):
    settings.local_source_path = str(tmp_path)
    try:
        assert fetch_file_content("no/such/file.py") is None
    finally:
        settings.local_source_path = ""


def test_fetch_files_returns_dict_of_found_files(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a/found.py").write_text("code", encoding="utf-8")

    settings.local_source_path = str(tmp_path)
    try:
        result = fetch_files(["a/found.py", "b/missing.py"])
        assert "a/found.py" in result
        assert "b/missing.py" not in result
    finally:
        settings.local_source_path = ""


# --- GitHub PR 생성 ---


def _mock_repo():
    return MagicMock()


@patch("app.services.github_service._get_repo")
def test_create_pull_request_returns_pr_url(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    existing = MagicMock()
    existing.sha = "file_sha"
    repo.get_contents.return_value = existing

    pr = MagicMock()
    pr.html_url = "https://github.com/owner/repo/pull/1"
    repo.create_pull.return_value = pr

    url = create_pull_request(
        files=[{"path": "backend/app/main.py", "content": "fixed"}],
        summary="fix error",
        pr_body="body",
        branch_name="fix/error-abc-123",
    )
    assert url == "https://github.com/owner/repo/pull/1"
    repo.create_git_ref.assert_called_once()
    repo.update_file.assert_called_once()


@patch("app.services.github_service._get_repo")
def test_create_pull_request_reuses_existing_branch(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    repo.create_git_ref.side_effect = GithubException(422, "already exists", None)

    existing = MagicMock()
    existing.sha = "file_sha"
    repo.get_contents.return_value = existing

    pr = MagicMock()
    pr.html_url = "https://github.com/owner/repo/pull/2"
    repo.create_pull.return_value = pr

    url = create_pull_request(
        files=[{"path": "backend/app/main.py", "content": "fixed"}],
        summary="fix error",
        pr_body="body",
        branch_name="fix/error-abc-123",
    )
    assert url == "https://github.com/owner/repo/pull/2"
