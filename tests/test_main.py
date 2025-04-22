from unittest.mock import Mock, patch

import pytest

from src.main import open_issue_event, run, scan_issue_event


@pytest.fixture
def mock_issue():
    """Create a mock GitHub issue."""
    issue = Mock()
    issue.number = 1
    issue.title = "Original title"
    issue.body = "Issue description"
    issue.labels = []
    issue.created_at = None
    issue.pull_request = None
    return issue


@pytest.fixture
def mock_repo():
    """Create a mock GitHub repository."""
    repo = Mock()
    return repo


@pytest.fixture
def mock_config():
    config = Mock()
    config.ai_provider = "gemini"
    config.model_name = "gemini-2.0-flash"
    config.get_api_key.return_value = "fake_key"
    config.strip_characters = None
    # Use a safer approach for sensitive credentials in tests
    config.github_token = "DUMMY_TOKEN_FOR_TESTING"  # noqa: S105
    config.repo_name = "owner/repo"
    config.days_to_scan = 7
    config.max_issues = 10
    config.auto_update = False
    config.prompt = "Test prompt for {original_title} and {issue_body}"
    config.skip_label = "titled"
    config.is_issue_event = False
    config.issue_number = None
    return config


@pytest.fixture
def mock_ai_client():
    client = Mock()
    client.generate_content.return_value = "Improved title"
    return client


@pytest.fixture
def mock_github_client():
    client = Mock()
    return client


def test_open_issue_event(mock_config, mock_ai_client, mock_github_client, mock_repo, mock_issue):
    mock_config.issue_number = 1
    mock_repo.get_issue.return_value = mock_issue

    results = open_issue_event(mock_config, mock_repo, mock_ai_client, mock_github_client)

    mock_repo.get_issue.assert_called_once_with(1)
    assert len(results) == 1
    assert results[0]["improved_title"] == "Improved title"
    assert results[0]["issue_number"] == 1


def test_open_issue_event_error(mock_config, mock_ai_client, mock_github_client, mock_repo):
    mock_config.issue_number = 1
    mock_repo.get_issue.side_effect = Exception("Issue not found")

    results = open_issue_event(mock_config, mock_repo, mock_ai_client, mock_github_client)

    mock_repo.get_issue.assert_called_once_with(1)
    assert len(results) == 0


def test_scan_issue_event_no_issues(mock_config, mock_ai_client, mock_github_client, mock_repo):
    mock_github_client.get_recent_issues.return_value = []

    results = scan_issue_event(mock_config, mock_repo, mock_ai_client, mock_github_client)

    mock_github_client.get_recent_issues.assert_called_once_with(
        repo=mock_repo, days_to_scan=mock_config.days_to_scan, limit=mock_config.max_issues
    )
    assert len(results) == 0


def test_scan_issue_event_with_issues(
    mock_config, mock_ai_client, mock_github_client, mock_repo, mock_issue
):
    mock_github_client.get_recent_issues.return_value = [mock_issue]

    results = scan_issue_event(mock_config, mock_repo, mock_ai_client, mock_github_client)

    mock_github_client.get_recent_issues.assert_called_once_with(
        repo=mock_repo, days_to_scan=mock_config.days_to_scan, limit=mock_config.max_issues
    )
    assert len(results) == 1
    assert results[0]["issue_number"] == 1


@patch("src.main.Config")
@patch("src.main.create_ai_client")
@patch("src.main.GitHubClient")
@patch("src.main.open_issue_event")
def test_run_issue_event(
    mock_open_issue,
    mock_github_client_cls,
    mock_create_ai,
    mock_config_cls,
    mock_config,
    mock_ai_client,
    mock_github_client,
    mock_repo,
):
    mock_config_cls.return_value = mock_config
    mock_config.is_issue_event = True
    mock_config.issue_number = 1

    mock_create_ai.return_value = mock_ai_client
    mock_github_client_cls.return_value = mock_github_client
    mock_github_client.get_repository.return_value = mock_repo

    run()

    mock_config.validate.assert_called_once()
    mock_create_ai.assert_called_once_with(
        provider=mock_config.ai_provider,
        api_key=mock_config.get_api_key(),
        model_name=mock_config.model_name,
    )
    mock_github_client_cls.assert_called_once_with(mock_config.github_token)
    mock_github_client.get_repository.assert_called_once_with(mock_config.repo_name)
    mock_open_issue.assert_called_once_with(
        mock_config, mock_repo, mock_ai_client, mock_github_client
    )


@patch("src.main.Config")
def test_run_error(mock_config_cls, mock_config):
    mock_config_cls.return_value = mock_config
    mock_config.validate.side_effect = ValueError("Test error")

    with pytest.raises(SystemExit) as excinfo:
        run()

    assert excinfo.value.code == 1
