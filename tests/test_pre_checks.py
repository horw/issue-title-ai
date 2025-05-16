from unittest.mock import Mock, patch

import pytest

from src.core.pre_checks import block_user_title_edit


@pytest.fixture
def mock_event_data():
    """Create mock event data for edited issue title."""
    return {
        "action": "edited",
        "sender": {"type": "User"},
        "changes": {"title": {"from": "Original Title"}},
        "issue": {"labels": [{"name": "titled"}]},
    }


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    client = Mock()
    client.add_issue_comment = Mock()
    return client


@pytest.fixture
def mock_issue():
    """Create a mock GitHub issue."""
    issue = Mock()
    issue.edit = Mock()
    return issue


def test_block_user_title_edit_success(mock_event_data, mock_github_client, mock_issue):
    """Test successful blocking of a user title edit."""
    result = block_user_title_edit(mock_event_data, "titled", mock_github_client, mock_issue)

    # Assert the function returns True
    assert result is True

    # Assert comment was added with correct message
    mock_github_client.add_issue_comment.assert_called_once_with(
        mock_issue, "This issue has already been processed. Please do not change the title."
    )

    # Assert title was reverted back to the original
    mock_issue.edit.assert_called_once_with(title="Original Title")


def test_block_user_title_edit_not_edited_action(mock_event_data, mock_github_client, mock_issue):
    """Test when action is not 'edited'."""
    mock_event_data["action"] = "created"

    result = block_user_title_edit(mock_event_data, "titled", mock_github_client, mock_issue)

    assert result is False
    mock_github_client.add_issue_comment.assert_not_called()
    mock_issue.edit.assert_not_called()


def test_block_user_title_edit_not_user(mock_event_data, mock_github_client, mock_issue):
    """Test when sender is not a User."""
    mock_event_data["sender"]["type"] = "Bot"

    result = block_user_title_edit(mock_event_data, "titled", mock_github_client, mock_issue)

    assert result is False
    mock_github_client.add_issue_comment.assert_not_called()
    mock_issue.edit.assert_not_called()


def test_block_user_title_edit_no_previous_title(mock_event_data, mock_github_client, mock_issue):
    """Test when there is no previous title."""
    mock_event_data["changes"]["title"]["from"] = ""

    result = block_user_title_edit(mock_event_data, "titled", mock_github_client, mock_issue)

    assert result is False
    mock_github_client.add_issue_comment.assert_not_called()
    mock_issue.edit.assert_not_called()


def test_block_user_title_edit_no_skip_label(mock_event_data, mock_github_client, mock_issue):
    """Test when the issue doesn't have the skip label."""
    mock_event_data["issue"]["labels"] = [{"name": "bug"}]

    result = block_user_title_edit(mock_event_data, "titled", mock_github_client, mock_issue)

    assert result is False
    mock_github_client.add_issue_comment.assert_not_called()
    mock_issue.edit.assert_not_called()
