import datetime
from unittest.mock import Mock, patch

import pytest

from src.core.github_client import GitHubClient


def test_init_without_token():
    with pytest.raises(ValueError, match="GitHub token not provided"):
        GitHubClient("")


def test_get_repository_success():
    mock_github = Mock()
    mock_repo = Mock()
    mock_github.get_repo.return_value = mock_repo

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        repo = client.get_repository("owner/repo")

        assert repo == mock_repo
        mock_github.get_repo.assert_called_once_with("owner/repo")


def test_get_repository_error():
    mock_github = Mock()
    mock_github.get_repo.side_effect = Exception("Repository not found")

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")

        with pytest.raises(Exception, match="Repository not found"):
            client.get_repository("owner/repo")


def test_get_recent_issues():
    mock_github = Mock()
    mock_repo = Mock()

    # Create mock issues
    mock_issue1 = Mock()
    mock_issue1.created_at = datetime.datetime.now()
    mock_issue1.pull_request = None

    mock_issue2 = Mock()
    mock_issue2.created_at = datetime.datetime.now() - datetime.timedelta(days=10)
    mock_issue2.pull_request = None

    mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        issues = client.get_recent_issues(mock_repo, days_to_scan=5, limit=10)

        assert len(issues) == 1
        assert issues[0] == mock_issue1


def test_get_recent_issues_error():
    mock_github = Mock()
    mock_repo = Mock()
    mock_repo.get_issues.side_effect = Exception("API error")

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")

        with pytest.raises(Exception, match="API error"):
            client.get_recent_issues(mock_repo)


def test_update_issue_title_success():
    mock_github = Mock()
    mock_issue = Mock()

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        result = client.update_issue_title(mock_issue, "New Title")

        assert result is True
        mock_issue.edit.assert_called_once_with(title="New Title")


def test_update_issue_title_error():
    mock_github = Mock()
    mock_issue = Mock()
    mock_issue.edit.side_effect = Exception("API error")

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")

        with pytest.raises(Exception, match="API error"):
            client.update_issue_title(mock_issue, "New Title")


def test_add_issue_comment_success():
    mock_github = Mock()
    mock_issue = Mock()
    mock_comment = Mock()
    mock_issue.create_comment.return_value = mock_comment

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        result = client.add_issue_comment(mock_issue, "Test comment")

        assert result == mock_comment
        mock_issue.create_comment.assert_called_once_with("Test comment")


def test_add_issue_comment_error():
    mock_github = Mock()
    mock_issue = Mock()
    mock_issue.create_comment.side_effect = Exception("API error")

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")

        with pytest.raises(Exception, match="API error"):
            client.add_issue_comment(mock_issue, "Test comment")


def test_add_issue_label_success():
    mock_github = Mock()
    mock_issue = Mock()

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        result = client.add_issue_label(mock_issue, "enhancement")

        assert result is True
        mock_issue.add_to_labels.assert_called_once_with("enhancement")


def test_add_issue_label_error():
    mock_github = Mock()
    mock_issue = Mock()
    mock_issue.add_to_labels.side_effect = Exception("API error")

    with patch("src.core.github_client.Github", return_value=mock_github):
        client = GitHubClient("valid-token")
        result = client.add_issue_label(mock_issue, "enhancement")

        assert result is False
