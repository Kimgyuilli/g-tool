from unittest.mock import MagicMock, patch

from github import GithubException

from app.services.github_service import add_issue_comment, create_issue, create_pull_request, find_open_issue_by_key


def _mock_repo():
    return MagicMock()


@patch("app.services.github_service._get_repo")
def test_create_pull_request_returns_pr_url(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    base_tree = MagicMock()
    repo.get_git_tree.return_value = base_tree

    new_tree = MagicMock()
    repo.create_git_tree.return_value = new_tree

    parent_commit = MagicMock()
    repo.get_git_commit.return_value = parent_commit

    new_commit = MagicMock()
    new_commit.sha = "new_sha"
    repo.create_git_commit.return_value = new_commit

    branch_ref = MagicMock()
    repo.get_git_ref.return_value = branch_ref

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
    repo.create_git_tree.assert_called_once()
    repo.create_git_commit.assert_called_once()


@patch("app.services.github_service._get_repo")
def test_create_pull_request_reuses_existing_branch(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    repo.create_git_ref.side_effect = GithubException(422, "already exists", None)

    base_tree = MagicMock()
    repo.get_git_tree.return_value = base_tree

    new_tree = MagicMock()
    repo.create_git_tree.return_value = new_tree

    parent_commit = MagicMock()
    repo.get_git_commit.return_value = parent_commit

    new_commit = MagicMock()
    new_commit.sha = "new_sha"
    repo.create_git_commit.return_value = new_commit

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


@patch("app.services.github_service._get_repo")
def test_find_open_issue_by_key_returns_existing_issue(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    issue = MagicMock()
    issue.title = "[abc1234567] pull_request_failed - RuntimeError"
    issue.created_at = None
    repo.get_issues.return_value = [issue]

    found = find_open_issue_by_key("abc1234567", ["auto-fix-failed"])

    assert found is issue


@patch("app.services.github_service._get_repo")
def test_create_issue_returns_issue_url(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo
    issue = MagicMock()
    issue.html_url = "https://github.com/owner/repo/issues/1"
    repo.create_issue.return_value = issue

    url = create_issue("title", "body", ["auto-fix-failed"])

    assert url == "https://github.com/owner/repo/issues/1"


def test_add_issue_comment_returns_issue_url():
    issue = MagicMock()
    issue.html_url = "https://github.com/owner/repo/issues/1"

    url = add_issue_comment(issue, "comment body")

    assert url == "https://github.com/owner/repo/issues/1"
    issue.create_comment.assert_called_once_with("comment body")
