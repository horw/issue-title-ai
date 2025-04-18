from unittest.mock import Mock, patch

import pytest

from src.core.llm import DeepseekAIClient, GeminiAIClient, OpenAIClient, create_ai_client


def test_gemini_init_with_api_key():
    with patch("google.generativeai.configure") as mock_configure:
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            GeminiAIClient("valid-key", "gemini-2.0-flash")
            mock_configure.assert_called_once_with(api_key="valid-key")
            mock_model_cls.assert_called_once_with("gemini-2.0-flash")


def test_gemini_init_without_api_key():
    with pytest.raises(ValueError, match="Gemini API key not provided"):
        GeminiAIClient("", "gemini-2.0-flash")


def test_gemini_generate_content():
    mock_response = Mock()
    mock_response.text = "Generated response"

    mock_model = Mock()
    mock_model.generate_content.return_value = mock_response

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel", return_value=mock_model):
            client = GeminiAIClient("valid-key", "gemini-2.0-flash")
            result = client.generate_content("Test prompt")

            assert result == "Generated response"
            mock_model.generate_content.assert_called_once_with("Test prompt")


def test_gemini_generate_content_error():
    mock_model = Mock()
    mock_model.generate_content.side_effect = Exception("API error")

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel", return_value=mock_model):
            client = GeminiAIClient("valid-key", "gemini-2.0-flash")

            with pytest.raises(Exception, match="API error"):
                client.generate_content("Test prompt")


def test_openai_init_with_api_key():
    with patch("openai.OpenAI") as mock_openai:
        client = OpenAIClient("valid-key", "gpt-4")

        mock_openai.assert_called_once_with(api_key="valid-key")
        assert client.model_name == "gpt-4"


def test_openai_init_without_api_key():
    with pytest.raises(ValueError, match="OpenAI API key not provided"):
        OpenAIClient("", "gpt-4")


def test_openai_generate_content():
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated response"))]

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        client = OpenAIClient("valid-key", "gpt-4")
        result = client.generate_content("Test prompt")

        assert result == "Generated response"
        mock_client.chat.completions.create.assert_called_once()


def test_openai_generate_content_error():
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch("openai.OpenAI", return_value=mock_client):
        client = OpenAIClient("valid-key", "gpt-4")

        with pytest.raises(Exception, match="API error"):
            client.generate_content("Test prompt")


def test_deepseek_init_with_api_key():
    with patch("openai.OpenAI") as mock_openai:
        client = DeepseekAIClient("valid-key", "deepseek-chat")

        mock_openai.assert_called_once_with(
            api_key="valid-key", base_url="https://api.deepseek.com/v1"
        )
        assert client.model_name == "deepseek-chat"


def test_deepseek_init_without_api_key():
    with pytest.raises(ValueError, match="Deepseek API key not provided"):
        DeepseekAIClient("", "deepseek-chat")


def test_deepseek_generate_content():
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated response"))]

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        client = DeepseekAIClient("valid-key", "deepseek-chat")
        result = client.generate_content("Test prompt")

        assert result == "Generated response"
        mock_client.chat.completions.create.assert_called_once()


def test_deepseek_generate_content_error():
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch("openai.OpenAI", return_value=mock_client):
        client = DeepseekAIClient("valid-key", "deepseek-chat")

        with pytest.raises(Exception, match="API error"):
            client.generate_content("Test prompt")


def test_create_ai_client_gemini():
    with patch("src.core.llm.GeminiAIClient") as mock_gemini:
        create_ai_client("gemini", "api-key", "model-name")
        mock_gemini.assert_called_once_with("api-key", "model-name")


def test_create_ai_client_openai():
    with patch("src.core.llm.OpenAIClient") as mock_openai:
        create_ai_client("openai", "api-key", "model-name")
        mock_openai.assert_called_once_with("api-key", "model-name")


def test_create_ai_client_deepseek():
    with patch("src.core.llm.DeepseekAIClient") as mock_deepseek:
        create_ai_client("deepseek", "api-key", "model-name")
        mock_deepseek.assert_called_once_with("api-key", "model-name")


def test_create_ai_client_default_model():
    with patch("src.core.llm.GeminiAIClient") as mock_gemini:
        create_ai_client("gemini", "api-key")
        mock_gemini.assert_called_once_with("api-key", "gemini-2.0-flash")

    with patch("src.core.llm.OpenAIClient") as mock_openai:
        create_ai_client("openai", "api-key")
        mock_openai.assert_called_once_with("api-key", "gpt-4")

    with patch("src.core.llm.DeepseekAIClient") as mock_deepseek:
        create_ai_client("deepseek", "api-key")
        mock_deepseek.assert_called_once_with("api-key", "deepseek-chat")


def test_create_ai_client_unsupported():
    with pytest.raises(ValueError, match="Unsupported AI provider: invalid"):
        create_ai_client("invalid", "api-key")
