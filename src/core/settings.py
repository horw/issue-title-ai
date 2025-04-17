import os


class Config:
    def __init__(self):
        self.github_token = os.environ.get("INPUT_GITHUB-TOKEN")
        self.repo_name = os.environ.get("GITHUB_REPOSITORY")
        self.days_to_scan = int(os.environ.get("INPUT_DAYS-TO-SCAN", "7"))
        self.auto_update = os.environ.get("INPUT_AUTO-UPDATE", "false").lower() == "true"
        self.max_issues = int(os.environ.get("INPUT_MAX-ISSUES", "100"))

        self.gemini_api_key = os.environ.get("INPUT_GEMINI-API-KEY")
        self.openai_api_key = os.environ.get("INPUT_OPENAI-API-KEY")
        self.deepseek_api_key = os.environ.get("INPUT_DEEPSEEK-API-KEY")
        self.providers = {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
        }
        self.explicit_provider = os.environ.get("INPUT_AI-PROVIDER", "").lower()

        self.model_name = os.environ.get("INPUT_MODEL")
        self.prompt = os.environ.get(
            "INPUT_PROMPT",
            """
You are an expert at writing clear, concise, and descriptive GitHub issue titles.
Please analyze the following issue title and determine if it needs improvement.
If the title is already clear, specific, and well-formatted, return the original title unchanged.
Otherwise, improve it to make it more specific, actionable, and easy to understand.
The improved title should clearly communicate the problem or feature request.

Original Issue Title: "{original_title}"

Issue Description:
\"\"\"
{issue_body}
\"\"\"

Rules for a good issue title:
1. Be specific and descriptive
2. Use action verbs when appropriate
3. Include relevant context (component name, page, feature)
4. Keep it concise (under 80 characters ideally)
5. Avoid vague terms like "bug" or "issue" without context
6. Don't change the meaning or intent of the original issue
7. If the original title is already good enough, do not change it

Your response should ONLY contain the improved issue title
or the original title if it's already good.
Do not include any other text or explanations.
""",
        )
        self.skip_label = os.environ.get("INPUT_SKIP-LABEL", "titled")

        # Check if this is an issue event trigger
        self.event_name = os.environ.get("GITHUB_EVENT_NAME")
        self.event_path = os.environ.get("GITHUB_EVENT_PATH")
        self.is_issue_event = self.event_name == "issues"
        self.issue_number = None

        # If it's an issue event, get the issue number
        if self.is_issue_event and self.event_path and os.path.exists(self.event_path):
            try:
                import json

                with open(self.event_path) as f:
                    event_data = json.load(f)
                    if "issue" in event_data and "number" in event_data["issue"]:
                        self.issue_number = event_data["issue"]["number"]
            except Exception as e:
                print(f"Error parsing event data: {e!s}")

        self.ai_provider = self._detect_ai_provider()

    def _detect_ai_provider(self):
        explicit = os.environ.get("INPUT_AI-PROVIDER", "").lower()
        if explicit in self.providers:
            if not self.providers[explicit]:
                raise ValueError(f"{self.providers[explicit]} API key not provided")
            return explicit

        for provider, api_key in self.providers.items():
            if api_key:
                return provider

        raise ValueError(
            "No LLM API key was provided. Please provide one of the following: deepseek, gemini, openai."
        )

    def get_api_key(self):
        return self.providers[self.ai_provider]

    def validate(self):
        if not self.github_token:
            raise ValueError("GitHub token is required")

        if not self.repo_name:
            raise ValueError("GitHub repository name is required")

        if not self.get_api_key():
            raise ValueError(f"API key not found for {self.ai_provider}")
