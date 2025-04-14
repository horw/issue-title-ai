"""IssueTitleAI: GitHub issue title improvement tool.

A single-file implementation that analyzes GitHub issue titles and suggests improvements
or automatically updates them based on configuration.
"""

import datetime
import os
import sys
from abc import ABC, abstractmethod

import google.generativeai as genai
import openai
from github import Github


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
        self.model_name = os.environ.get("INPUT_MODEL")

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
        if explicit == "gemini" and self.gemini_api_key:
            return "gemini"
        if explicit == "openai" and self.openai_api_key:
            return "openai"
        if explicit == "deepseek" and self.deepseek_api_key:
            return "deepseek"

        if self.gemini_api_key:
            return "gemini"
        if self.deepseek_api_key:
            return "deepseek"
        if self.openai_api_key:
            return "openai"

        return "gemini"

    def get_api_key(self):
        if self.ai_provider == "gemini":
            return self.gemini_api_key
        if self.ai_provider == "deepseek":
            return self.deepseek_api_key
        return self.openai_api_key

    def validate(self):
        if not self.github_token:
            raise ValueError("GitHub token is required")

        if not self.repo_name:
            raise ValueError("GitHub repository name is required")

        if not self.get_api_key():
            raise ValueError(f"API key not found for {self.ai_provider}")


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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at improving GitHub issue titles.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at improving GitHub issue titles.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating content with Deepseek: {e!s}")
            raise


def create_ai_client(provider, api_key=None, model_name=None):
    if provider.lower() == "gemini":
        return GeminiAIClient(api_key, model_name or "gemini-2.0-flash")
    elif provider.lower() == "openai":
        return OpenAIClient(api_key, model_name or "gpt-4")
    elif provider.lower() == "deepseek":
        return DeepseekAIClient(api_key, model_name or "deepseek-chat")
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")


class GitHubClient:
    def __init__(self, token):
        if not token:
            raise ValueError("GitHub token not provided")
        self.client = Github(token)

    def get_repository(self, repo_name):
        try:
            return self.client.get_repo(repo_name)
        except Exception as e:
            print(f"Error accessing repository {repo_name}: {e!s}")
            raise

    def get_recent_issues(self, repo, days_to_scan=7, limit=100):
        date_threshold = datetime.datetime.now() - datetime.timedelta(days=days_to_scan)

        try:
            all_issues = repo.get_issues(state="open", sort="created", direction="desc")

            recent_issues = []
            for issue in all_issues:
                if issue.created_at >= date_threshold and not issue.pull_request:
                    recent_issues.append(issue)
                if len(recent_issues) >= limit:
                    break

            return recent_issues
        except Exception as e:
            print(f"Error fetching recent issues: {e!s}")
            raise

    def update_issue_title(self, issue, new_title):
        try:
            issue.edit(title=new_title)
            return True
        except Exception as e:
            print(f"Error updating issue title: {e!s}")
            raise

    def add_issue_comment(self, issue, comment_text):
        try:
            return issue.create_comment(comment_text)
        except Exception as e:
            print(f"Error adding comment to issue: {e!s}")
            raise

    def add_issue_label(self, issue, label_name):
        try:
            issue.add_to_labels(label_name)
            return True
        except Exception as e:
            print(f"Error adding label to issue: {e!s}")
            return False


class IssueProcessor:
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def process_issue(self, issue, github_client, auto_update=False):
        issue_number = issue.number
        original_title = issue.title
        issue_body = issue.body or ""

        # Check if issue has the "titled" label
        labels = [label.name.lower() for label in issue.labels]
        if "titled" in labels:
            print(f"Skipping issue #{issue_number}: Already has 'titled' label")
            return {
                "issue_number": issue_number,
                "original_title": original_title,
                "improved_title": None,
                "updated": False,
                "skipped": True,
                "reason": "Has 'titled' label",
            }

        print(f'Processing issue #{issue_number}: "{original_title}"')

        try:
            improved_title = self.generate_improved_title(original_title, issue_body)

            if improved_title == original_title or not improved_title:
                print(f"Title already optimal for issue #{issue_number}")
                return {
                    "issue_number": issue_number,
                    "original_title": original_title,
                    "improved_title": None,
                    "updated": False,
                }

            if auto_update:
                github_client.update_issue_title(issue, improved_title)

                comment = (
                    f"🤖 I've improved the title of this issue "
                    f"for better clarity and discoverability.\n\n"
                    f"**Previous title:** {original_title}\n"
                    f"**New title:** {improved_title}"
                )
                github_client.add_issue_comment(issue, comment)

                print(f'Updated issue #{issue_number} title to: "{improved_title}"')
            else:
                comment = (
                    f"🤖 I've analyzed this issue title "
                    f"and have a suggestion for improvement:\n\n"
                    f"**Current title:** {original_title}\n"
                    f"**Suggested title:** {improved_title}\n\n"
                )
                github_client.add_issue_comment(issue, comment)

                print(f"Added title suggestion to issue #{issue_number}")

            # Add the 'titled' label to the issue after processing
            github_client.add_issue_label(issue, "titled")
            print(f"Added 'titled' label to issue #{issue_number}")

            return {
                "issue_number": issue_number,
                "original_title": original_title,
                "improved_title": improved_title,
                "updated": auto_update,
            }

        except Exception as error:
            print(f"Warning: Error processing issue #{issue_number}: {error!s}")
            return {"issue_number": issue_number, "error": str(error)}

    def generate_improved_title(self, original_title, issue_body):
        prompt = f"""
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
"""

        return self.ai_client.generate_content(prompt)


def open_issue_event(config, repo_obj, ai_client, github_client):
    print(f"Processing single issue #{config.issue_number} from event trigger")
    try:
        issue = repo_obj.get_issue(config.issue_number)
        issue_processor = IssueProcessor(ai_client)
        result = issue_processor.process_issue(
            issue=issue, github_client=github_client, auto_update=config.auto_update
        )
        return [result]
    except Exception as e:
        print(f"Error processing issue #{config.issue_number}: {e!s}")
        return []


def scan_issue_event(config, repo_obj, ai_client, github_client):
    # Regular scheduled run - process all recent issues
    recent_issues = github_client.get_recent_issues(
        repo=repo_obj, days_to_scan=config.days_to_scan, limit=config.max_issues
    )

    if not recent_issues:
        print(f"No open issues found in the last {config.days_to_scan} days")
        return []

    print(f"Found {len(recent_issues)} issues to process")

    issue_processor = IssueProcessor(ai_client)

    results = []
    for i, issue in enumerate(recent_issues, 1):
        print(f"[{i}/{len(recent_issues)}] Processing issue #{issue.number}")
        result = issue_processor.process_issue(
            issue=issue, github_client=github_client, auto_update=config.auto_update
        )
        results.append(result)

    improved_count = len([r for r in results if r.get("improved_title")])
    print(f"Summary: {improved_count} of {len(recent_issues)} issues improved")
    return results


def run():
    try:
        config = Config()
        config.validate()

        print(f"Using {config.ai_provider} with model: {config.model_name}")

        ai_client = create_ai_client(
            provider=config.ai_provider, api_key=config.get_api_key(), model_name=config.model_name
        )

        github_client = GitHubClient(config.github_token)

        if not config.repo_name:
            print("Error: Repository name not found")
            sys.exit(1)

        print(f"Scanning repository: {config.repo_name}")
        repo_obj = github_client.get_repository(config.repo_name)

        # If this is triggered by an issue event, process only that specific issue
        if config.is_issue_event and config.issue_number:
            open_issue_event(config, repo_obj, ai_client, github_client)
        else:
            scan_issue_event(config, repo_obj, ai_client, github_client)

    except Exception as error:
        print(f"Error: {error!s}")
        sys.exit(1)


if __name__ == "__main__":
    run()
