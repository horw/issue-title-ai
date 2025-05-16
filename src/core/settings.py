import os
import re
import random

class Config:
    def __init__(self):
        self.github_token = os.environ.get("INPUT_GITHUB-TOKEN")
        self.repo_name = os.environ.get("GITHUB_REPOSITORY")
        self.days_to_scan = int(os.environ.get("INPUT_DAYS-TO-SCAN", "7"))
        self.auto_update = os.environ.get("INPUT_AUTO-UPDATE", "false").lower() == "true"
        self.quiet = os.environ.get("INPUT_QUIET", "false").lower() == "true"
        self.max_issues = int(os.environ.get("INPUT_MAX-ISSUES", "100"))
        self.required_labels = self._parse_labels(os.environ.get("INPUT_REQUIRED-LABELS", ""))
        self.apply_to_closed = os.environ.get("INPUT_APPLY-TO-CLOSED", "false").lower() == "true"
        self.ai_providers = self._get_llm_configs()

        self.verbose = os.environ.get("INPUT_VERBOSE", "false").lower() == "true"
        self.strip_characters = os.environ.get("INPUT_STRIP-CHARACTERS")

        self.prompt = self._retrieve_prompt()
        self.skip_label = os.environ.get("INPUT_SKIP-LABEL", "titled")

        # Check if this is an issue event trigger
        self.event_name = os.environ.get("GITHUB_EVENT_NAME")
        self.event_path = os.environ.get("GITHUB_EVENT_PATH")
        self.is_issue_event = self.event_name == "issues"
        self.issue_number = None
        self.event_data = None

        # If it's an issue event, get the issue number
        if self.is_issue_event and self.event_path and os.path.exists(self.event_path):
            try:
                import json

                with open(self.event_path) as f:
                    event_data = json.load(f)
                    self.event_data = event_data
                    if "issue" in event_data and "number" in event_data["issue"]:
                        self.issue_number = event_data["issue"]["number"]
            except Exception as e:
                print(f"Error parsing event data: {e!s}")
        self.validate()

    def _retrieve_prompt(self):
        prompt = os.environ.get("INPUT_PROMPT")
        if prompt:
            return prompt
        style = os.environ.get("INPUT_STYLE", "summary")

        styles_dir = os.path.join(os.path.dirname(__file__), "..", "..", "styles")

        all_files = os.listdir(styles_dir)
        style_files = [f for f in all_files if not f.startswith("_")]
        include_files = [f for f in all_files if f.startswith("_")]

        matched_file = None
        for filename in style_files:
            if os.path.splitext(filename)[0] == style:
                matched_file = filename
                break

        if not matched_file:
            available_styles = [os.path.splitext(f)[0] for f in style_files]
            raise Exception(
                f"Style {style} is not supported, please use one of {', '.join(available_styles)}"
            )

        prompt_content = self._process_style_file(
            os.path.join(styles_dir, matched_file), include_files, styles_dir
        )
        return prompt_content

    def _process_style_file(self, file_path, include_files, styles_dir):
        """Process a style file and handle any includes."""
        with open(file_path) as file:
            content = file.read()

        def replace_include(match):
            include_path = match.group(1).strip()
            if include_path not in include_files:
                raise Exception(f"Included file {include_path} doesn't exist, please use one of {', '.join(include_files)}")

            full_path = os.path.join(styles_dir, include_path)
            with open(full_path) as include_file:
                return include_file.read()

        processed_content = re.sub(r"{include:(.*?)}", replace_include, content)
        return processed_content

    def _parse_labels(self, labels_str):
        """Parse comma-separated labels string into a list of labels."""
        if not labels_str:
            return []
        return [label.strip() for label in labels_str.split(",") if label.strip()]

    def _get_llm_configs(self):
        gemini_api_key   = os.environ.get("INPUT_GEMINI-API-KEY")
        openai_api_key   = os.environ.get("INPUT_OPENAI-API-KEY")
        deepseek_api_key = os.environ.get("INPUT_DEEPSEEK-API-KEY")

        ai_providers = {}
        if gemini_api_key:
            ai_providers["gemini"] = {
            "provider" : "gemini",
            "api_key"  : gemini_api_key,
            "model"    : os.environ.get("INPUT_GEMINI-MODEL")
        }
        if openai_api_key:
            ai_providers["openai"] = {
            "provider" : "openai",
            "api_key"  : openai_api_key,
            "model"    : os.environ.get("INPUT_OPENAI-MODEL")
        }
        if deepseek_api_key:
            ai_providers["deepseek"] = {
            "provider" : "deepseek",
            "api_key"  : deepseek_api_key,
            "model"    : os.environ.get("INPUT_DEEPSEEK-MODEL")
        }

        if not ai_providers:
            raise ValueError("No LLM API key was provided. Please provide one of the following: deepseek, gemini, openai.")

        explicit_provider = os.environ.get("INPUT_AI-PROVIDER", "").lower()
        if explicit_provider:
            if explicit_provider not in ai_providers:
                raise ValueError(f"API key not found for {explicit_provider}")
            ai_providers = {explicit_provider : ai_providers[explicit_provider]}

        return ai_providers

    @property
    def ai_provider(self):
        ai_provider_name = random.choice(list(self.ai_providers.keys())) # noqa: S311
        return self.ai_providers[ai_provider_name]

    def validate(self):
        if not self.github_token:
            raise ValueError("GitHub token is required")

        if not self.repo_name:
            raise ValueError("GitHub repository name is required")
