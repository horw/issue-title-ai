from abc import ABC, abstractmethod

import google.generativeai as genai
import openai

from .verbose import verbose_print


class AIClient(ABC):
    @abstractmethod
    def generate_content(self, prompt):
        pass


class GeminiAIClient(AIClient):
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key not provided")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_content(self, prompt):
        try:
            verbose_print(prompt)
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating content with Gemini: {e!s}")
            raise


class OpenAIClient(AIClient):
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.model_name = model_name

    def generate_content(self, prompt):
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at improving GitHub issue titles.",
                },
                {"role": "user", "content": prompt},
            ]
            verbose_print(self.model_name, messages)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            verbose_print("Model Usage", response.usage)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating content with OpenAI: {e!s}")
            raise


class DeepseekAIClient(AIClient):
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Deepseek API key not provided")

        self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
        self.model_name = model_name

    def generate_content(self, prompt):
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at improving GitHub issue titles.",
                },
                {"role": "user", "content": prompt},
            ]
            verbose_print(self.model_name, messages)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            verbose_print("Model Usage", response.usage)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating content with Deepseek: {e!s}")
            raise


def create_ai_client(provider, api_key, model_name=None):
    if provider.lower() == "gemini":
        return GeminiAIClient(api_key, model_name or "gemini-2.0-flash")
    elif provider.lower() == "openai":
        return OpenAIClient(api_key, model_name or "gpt-4")
    elif provider.lower() == "deepseek":
        return DeepseekAIClient(api_key, model_name or "deepseek-chat")
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
