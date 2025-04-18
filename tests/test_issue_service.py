from unittest.mock import Mock, patch

import pytest

from src.core.issue_service import IssueProcessor


@pytest.fixture
def processor():
    mock_ai_client = Mock()
    mock_github_client = Mock()
    prompt = "Test prompt for {original_title} and {issue_body}"
    skip_label = "titled"
    return IssueProcessor(mock_ai_client, mock_github_client, prompt, skip_label)


def test_process_issue_already_labeled(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"
    mock_label = Mock()
    mock_label.name = processor.skip_label
    mock_issue.labels = [mock_label]

    result = processor.process_issue(mock_issue)

    assert result["skipped"] is True


def test_process_issue_title_already_optimal(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Original title"

    result = processor.process_issue(mock_issue)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] is None
    assert result["updated"] is False

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body="Issue body"
    )
    assert expected_prompt == "Test prompt for Original title and Issue body"
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)


def test_process_issue_auto_update(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.process_issue(mock_issue, auto_update=True)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] == "Improved title"
    assert result["updated"] is True

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body="Issue body"
    )
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)

    processor.github_client.update_issue_title.assert_called_once_with(mock_issue, "Improved title")
    processor.github_client.add_issue_comment.assert_called_once()
    processor.github_client.add_issue_label.assert_called_once_with(
        mock_issue, processor.skip_label
    )


def test_process_issue_suggestion_only(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.process_issue(mock_issue, auto_update=False)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] == "Improved title"
    assert result["updated"] is False

    processor.github_client.update_issue_title.assert_not_called()
    processor.github_client.add_issue_comment.assert_called_once()
    processor.github_client.add_issue_label.assert_called_once_with(
        mock_issue, processor.skip_label
    )


def test_process_issue_error(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"
    mock_issue.labels = []

    processor.ai_client.generate_content.side_effect = Exception("API error")

    result = processor.process_issue(mock_issue)

    assert result["issue_number"] == 1
    assert result["error"] == "API error"


def test_generate_improved_title(processor):
    mock_issue = Mock()
    mock_issue.title = "Original title"
    mock_issue.body = "Issue body"

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.generate_improved_title(mock_issue.title, mock_issue.body)

    assert result == "Improved title"
    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body="Issue body"
    )
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)
