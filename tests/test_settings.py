import json
import os
from unittest.mock import mock_open, patch

import pytest

from src.core.settings import Config


@pytest.fixture
def mock_env():
    env_vars = {
        "INPUT_GITHUB-TOKEN": "test-token",
        "GITHUB_REPOSITORY": "owner/repo",
        "INPUT_DAYS-TO-SCAN": "5",
        "INPUT_AUTO-UPDATE": "true",
        "INPUT_MAX-ISSUES": "50",
        "INPUT_GEMINI-API-KEY": "test-gemini-key",
        "INPUT_OPENAI-API-KEY": "",
        "INPUT_DEEPSEEK-API-KEY": "",
        "INPUT_AI-PROVIDER": "gemini",
        "INPUT_MODEL": "gemini-2.0-flash",
        "INPUT_PROMPT": "Test prompt",
        "INPUT_SKIP-LABEL": "no-improve",
        "GITHUB_EVENT_NAME": "issues",
        "GITHUB_EVENT_PATH": "/path/to/event.json",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        yield


def test_config_init(mock_env):
    with patch("os.path.exists", return_value=True):
        event_data = {"issue": {"number": 123}}
        with patch("builtins.open", mock_open(read_data=json.dumps(event_data))):
            config = Config()

            assert config.github_token == "test-token"  # noqa: S105
            assert config.repo_name == "owner/repo"
            assert config.days_to_scan == 5
            assert config.auto_update is True
            assert config.max_issues == 50
            assert config.gemini_api_key == "test-gemini-key"
            assert config.openai_api_key == ""
            assert config.deepseek_api_key == ""
            assert config.ai_provider == "gemini"
            assert config.model_name == "gemini-2.0-flash"
            assert config.prompt == "Test prompt"
            assert config.skip_label == "no-improve"
            assert config.is_issue_event is True
            assert config.issue_number == 123


def test_config_defaults():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        config = Config()

        assert config.days_to_scan == 7  # Default
        assert config.auto_update is False  # Default
        assert config.max_issues == 100  # Default
        assert config.skip_label == "titled"  # Default
        assert config.is_issue_event is False  # Default


def test_detect_ai_provider_explicit():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
            "INPUT_AI-PROVIDER": "openai",
        },
        clear=True,
    ):
        config = Config()
        assert config.ai_provider == "openai"


def test_detect_ai_provider_implicit():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
        },
        clear=True,
    ):
        config = Config()
        assert config.ai_provider == "openai"


def test_detect_ai_provider_missing_explicit_key():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
            "INPUT_AI-PROVIDER": "gemini",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="None API key not provided"):
            Config()


def test_detect_ai_provider_no_keys():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="No LLM API key was provided"):
            Config()


def test_get_api_key():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
            "INPUT_AI-PROVIDER": "openai",
        },
        clear=True,
    ):
        config = Config()
        assert config.get_api_key() == "test-openai-key"


def test_validate_success():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        config = Config()
        # Should not raise any exceptions
        config.validate()


def test_validate_missing_github_token():
    with patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        config = Config()
        with pytest.raises(ValueError, match="GitHub token is required"):
            config.validate()


def test_validate_missing_repo_name():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        config = Config()
        with pytest.raises(ValueError, match="GitHub repository name is required"):
            config.validate()


def test_validate_missing_api_key():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
        },
        clear=True,
    ):
        with patch.object(Config, "_detect_ai_provider", return_value="gemini"):
            config = Config()
            with pytest.raises(ValueError, match="API key not found for gemini"):
                config.validate()


def test_event_data_parsing_error():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "GITHUB_EVENT_NAME": "issues",
            "GITHUB_EVENT_PATH": "/path/to/event.json",
        },
        clear=True,
    ):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                config = Config()

                assert config.issue_number is None


def test_retrieve_prompt_from_env():
    """Test retrieving prompt directly from INPUT_PROMPT env var."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_PROMPT": "Custom prompt from env",
        },
        clear=True,
    ):
        config = Config()
        assert config.prompt == "Custom prompt from env"


def test_retrieve_prompt_from_style_file():
    """Test retrieving prompt from style file when INPUT_PROMPT is not set."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_STYLE": "custom_style",
        },
        clear=True,
    ):
        mock_file_content = "This is a custom style prompt"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            config = Config()
            assert config.prompt == "This is a custom style prompt"


def test_retrieve_prompt_default_style():
    """Test retrieving prompt using default style when neither INPUT_PROMPT nor INPUT_STYLE are set."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        # Mock the file open and read operations
        mock_file_content = "This is the default style prompt"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            config = Config()
            assert config.prompt == "This is the default style prompt"


def test_retrieve_prompt_default_style_file_exists():
    """Test default style file exists."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        Config()


def test_parse_labels():
    """Test parsing of input labels."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        # Test with no labels
        config = Config()
        assert config.required_labels == []

    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_REQUIRED-LABELS": "bug, enhancement",
        },
        clear=True,
    ):
        # Test with multiple labels
        config = Config()
        assert config.required_labels == ["bug", "enhancement"]

    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_REQUIRED-LABELS": "bug",
        },
        clear=True,
    ):
        # Test with a single label
        config = Config()
        assert config.required_labels == ["bug"]

    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_REQUIRED-LABELS": " bug, , enhancement ",
        },
        clear=True,
    ):
        # Test with extra spaces and empty labels
        config = Config()
        assert config.required_labels == ["bug", "enhancement"]
