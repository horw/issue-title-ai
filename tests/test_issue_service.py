from unittest.mock import Mock, patch

import pytest

from src.core.issue_service import IssueProcessor

issue_body = "Issue body" * 30


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
    mock_issue.body = issue_body
    mock_label = Mock()
    mock_label.name = processor.skip_label
    mock_issue.labels = [mock_label]

    result = processor.process_issue(mock_issue)

    assert result["skipped"] is True


def test_process_issue_title_already_optimal(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = issue_body
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Original title"

    result = processor.process_issue(mock_issue)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] is None
    assert result["updated"] is False

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
    )
    assert expected_prompt == f"Test prompt for Original title and {issue_body}"
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)


def test_short_body(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = "Hello"
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Original title"

    result = processor.process_issue(mock_issue)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] is None
    assert result["updated"] is False
    assert result["reason"] == "Issue body too short"

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
    )
    assert expected_prompt == f"Test prompt for Original title and {issue_body}"


def test_process_issue_auto_update(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = issue_body
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.process_issue(mock_issue, auto_update=True)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] == "Improved title"
    assert result["updated"] is True

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
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
    mock_issue.body = issue_body
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
    mock_issue.body = issue_body
    mock_issue.labels = []

    processor.ai_client.generate_content.side_effect = Exception("API error")

    result = processor.process_issue(mock_issue)

    assert result["issue_number"] == 1
    assert result["error"] == "API error"


def test_generate_improved_title(processor):
    mock_issue = Mock()
    mock_issue.title = "Original title"
    mock_issue.body = issue_body

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.generate_improved_title(mock_issue.title, mock_issue.body)

    assert result == "Improved title"
    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
    )
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)


def test_quite(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = issue_body
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Improved title"

    result = processor.process_issue(mock_issue, auto_update=True, quiet=True)

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] == "Improved title"
    assert result["updated"] is True

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
    )
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)

    processor.github_client.update_issue_title.assert_called_once_with(mock_issue, "Improved title")
    processor.github_client.add_issue_comment.assert_not_called()
    processor.github_client.add_issue_label.assert_called_once_with(
        mock_issue, processor.skip_label
    )


def test_strip_chars(processor):
    mock_issue = Mock()
    mock_issue.number = 1
    mock_issue.title = "Original title"
    mock_issue.body = issue_body
    mock_issue.labels = []

    processor.ai_client.generate_content.return_value = "Improved titleHAHAHA"

    result = processor.process_issue(
        mock_issue, auto_update=True, quiet=True, strip_characters="HA"
    )

    assert result["issue_number"] == 1
    assert result["original_title"] == "Original title"
    assert result["improved_title"] == "Improved title"
    assert result["updated"] is True

    expected_prompt = processor.prompt.format(
        original_title="Original title", issue_body=issue_body
    )
    processor.ai_client.generate_content.assert_called_once_with(expected_prompt)

    processor.github_client.update_issue_title.assert_called_once_with(mock_issue, "Improved title")
    processor.github_client.add_issue_comment.assert_not_called()
    processor.github_client.add_issue_label.assert_called_once_with(
        mock_issue, processor.skip_label
    )


@pytest.mark.parametrize("required_labels", ([], ["bug", "enhancement"]))
def test_required_labels_filtering_should_process(required_labels):
    from unittest.mock import MagicMock

    from src.core.issue_service import IssueProcessor

    # Mock dependencies
    ai_client = MagicMock()
    github_client = MagicMock()
    prompt = "Test prompt"
    skip_label = "no-improve"

    # Test case: Issue has matching labels and should be processed
    issue_processor = IssueProcessor(ai_client, github_client, prompt, skip_label, required_labels)

    # Mock an issue with matching labels
    issue = MagicMock()
    issue.number = 123
    issue.title = "Original Issue Title"
    issue.body = issue_body

    # Create mock labels with name attributes that will match required_labels
    bug_label = MagicMock()
    bug_label.name = "bug"
    feature_label = MagicMock()
    feature_label.name = "feature"

    issue.labels = [bug_label, feature_label]

    # Patch the generate_improved_title method to avoid actual AI calls
    with patch.object(issue_processor, "generate_improved_title", return_value="Improved Title"):
        # Process the issue
        result = issue_processor.process_issue(issue)
        # Assert that the issue was processed and not skipped
        assert result["issue_number"] == 123
        assert result["original_title"] == "Original Issue Title"
        assert result["improved_title"] == "Improved Title"
        assert result.get("skipped") is None  # Not skipped


def test_required_labels_filtering_will_skip():
    """Test that issues are filtered correctly based on required labels."""
    from unittest.mock import MagicMock

    from src.core.issue_service import IssueProcessor

    ai_client = MagicMock()
    github_client = MagicMock()
    prompt = "Test prompt"
    skip_label = "no-improve"
    required_labels = ["bug", "enhancement"]

    # Test case: Issue has no matching labels and should be skipped
    issue_processor = IssueProcessor(ai_client, github_client, prompt, skip_label, required_labels)

    # Mock an issue with no matching labels
    issue = MagicMock()
    issue.number = 456
    issue.title = "Another Issue Title"
    issue.body = "Another issue body" * 30

    # Create mock labels with name attributes that won't match required_labels
    feature_label = MagicMock()
    feature_label.name = "feature"
    doc_label = MagicMock()
    doc_label.name = "documentation"

    issue.labels = [feature_label, doc_label]

    # Process the issue
    result = issue_processor.process_issue(issue)

    # Assert that the issue is skipped with the correct reason
    assert result["issue_number"] == 456
    assert result["original_title"] == "Another Issue Title"
    assert result["improved_title"] is None
    assert result["updated"] is False
    assert result["skipped"] is True
    assert "No matching labels found" in result["reason"]
