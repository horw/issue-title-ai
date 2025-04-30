import json
import os
import random
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
        "INPUT_GEMINI-MODEL": "gemini-2.0-flash",
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
            assert config.ai_provider == {
                "provider" : "gemini",
                "api_key"  : "test-gemini-key",
                "model"    : "gemini-2.0-flash"
            }
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
        assert config.ai_provider["provider"] == "openai"
        assert config.ai_provider["api_key"] == "test-openai-key"


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
        assert config.ai_provider["provider"] == "openai"
        assert config.ai_provider["api_key"] == "test-openai-key"


def test_detect_ai_provider_random():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
            "INPUT_DEEPSEEK-API-KEY": "test-deepseek-key",
        },
        clear=True,
    ):
        random.seed(1)
        llms_selected = {Config().ai_provider["provider"] for _ in range(100)}
        assert llms_selected == {"gemini", "openai", "deepseek"}


def test_detect_ai_provider_missing_explicit_key():
    ai_provider = "gemini"
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_OPENAI-API-KEY": "test-openai-key",
            "INPUT_AI-PROVIDER": ai_provider,
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match=f"API key not found for {ai_provider}"):
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


def test_validate_missing_github_token():
    with patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="GitHub token is required"):
            Config()


def test_validate_missing_repo_name():
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="GitHub repository name is required"):
            Config()

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
        with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="invalid json")):
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
            "INPUT_STYLE": "summary",
        },
        clear=True,
    ):
        mock_file_content = "This is a custom style prompt"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            config = Config()
            assert config.prompt == "This is a custom style prompt"


def test_retrieve_not_exists_prompt_from_style_file():
    """Test retrieving not exists prompt from style file when INPUT_PROMPT is not set."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_STYLE": "lala",
        },
        clear=True,
    ):
        with pytest.raises(Exception) as exc_info:
            _ = Config()
        assert "Style lala is not supported" in str(exc_info.value)


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


def test_config_apply_to_closed():
    """Test that apply-to-closed option is parsed correctly from environment variables."""
    # Test default value (false)
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
        assert not config.apply_to_closed

    # Test explicit value (true)
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_APPLY-TO-CLOSED": "true",
        },
        clear=True,
    ):
        config = Config()
        assert config.apply_to_closed

    # Test explicit value (false)
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_APPLY-TO-CLOSED": "false",
        },
        clear=True,
    ):
        config = Config()
        assert not config.apply_to_closed


def test_process_style_file():
    """Test the _process_style_file method with includes."""
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

        style_content = "# Title\n\n{include:_header.md}\n\n- Custom rule\n\n{include:_footer.md}"
        header_content = "Header content"
        footer_content = "Footer content"

        include_files = ["_header.md", "_footer.md"]
        styles_dir = os.path.normpath("/fake/path/to/styles")

        def mock_open_factory(files_dict):
            def _open_mock(filename, *args, **kwargs):
                for key, content in files_dict.items():
                    if filename.endswith(key):
                        return mock_open(read_data=content)(*args, **kwargs)

            return _open_mock

        mock_files = {
            os.path.normpath("/fake/path/to/styles/style.md"): style_content,
            os.path.normpath("/fake/path/to/styles/_header.md"): header_content,
            os.path.normpath("/fake/path/to/styles/_footer.md"): footer_content,
        }

        with patch("builtins.open", side_effect=mock_open_factory(mock_files)):
            result = config._process_style_file(
                os.path.join(styles_dir, "style.md"), include_files, styles_dir
            )

            expected = "# Title\n\nHeader content\n\n- Custom rule\n\nFooter content"
            assert result == expected


def test_process_style_file_missing_include():
    """Test the _process_style_file method with a non-existent include."""
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

        style_content = "# Title\n\n{include:_nonexistent.md}\n\n- Custom rule"

        include_files = ["_header.md", "_footer.md"]
        styles_dir = os.path.normpath("/fake/path/to/styles")

        with patch("builtins.open", mock_open(read_data=style_content)):
            with pytest.raises(Exception) as exc_info:
                config._process_style_file(
                    os.path.join(styles_dir, "style.md"), include_files, styles_dir
                )
            assert "_nonexistent.md doesn't exist" in str(exc_info.value)


def test_retrieve_prompt_with_includes():
    """Test retrieving a prompt that uses include directives."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_STYLE": "summary",
        },
        clear=True,
    ):
        all_files = ["summary.md", "order.md", "offense.md", "_header.md", "_footer.md"]

        summary_content = (
            "# Summary\n\n{include:_header.md}\n\n- Custom rule\n\n{include:_footer.md}"
        )
        header_content = "Header content"
        footer_content = "Footer content"

        with patch("os.listdir", return_value=all_files):

            def mock_open_factory(files_dict):
                def _open_mock(filename, *args, **kwargs):
                    for key, content in files_dict.items():
                        if filename.endswith(key):
                            return mock_open(read_data=content)(*args, **kwargs)

                return _open_mock

            mock_files = {
                "summary.md": summary_content,
                "_header.md": header_content,
                "_footer.md": footer_content,
            }

            with patch("builtins.open", side_effect=mock_open_factory(mock_files)):
                config = Config()
                expected = "# Summary\n\nHeader content\n\n- Custom rule\n\nFooter content"
                assert config.prompt == expected


def test_retrieve_prompt_handles_missing_include():
    """Test that _retrieve_prompt handles the case when an include file is missing."""
    with patch.dict(
        os.environ,
        {
            "INPUT_GITHUB-TOKEN": "test-token",
            "GITHUB_REPOSITORY": "owner/repo",
            "INPUT_GEMINI-API-KEY": "test-gemini-key",
            "INPUT_STYLE": "summary",
        },
        clear=True,
    ):
        all_files = ["summary.md", "order.md", "offense.md", "_header.md"]

        summary_content = (
            "# Summary\n\n{include:_header.md}\n\n- Custom rule\n\n{include:_footer.md}"
        )
        header_content = "Header content"

        with patch("os.listdir", return_value=all_files):

            def mock_open_factory(files_dict):
                def _open_mock(filename, *args, **kwargs):
                    for key, content in files_dict.items():
                        if filename.endswith(key):
                            return mock_open(read_data=content)(*args, **kwargs)

                return _open_mock

            mock_files = {
                "summary.md": summary_content,
                "_header.md": header_content,
            }

            with patch("builtins.open", side_effect=mock_open_factory(mock_files)):
                with pytest.raises(Exception) as exc_info:
                    Config()
                assert "_footer.md doesn't exist" in str(exc_info.value)
