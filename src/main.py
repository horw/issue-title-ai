"""IssueTitleAI: GitHub issue title improvement tool."""

import sys

from core.github_client import GitHubClient
from core.issue_service import IssueProcessor
from core.llm import create_ai_client
from core.pre_checks import block_user_title_edit
from core.settings import Config
from core.verbose import set_verbose


def pre_process(github_client, repo_obj, skip_label):
    existing_labels = github_client.get_labels(repo_obj)
    label_exists = any(label.name == skip_label for label in existing_labels)

    if not label_exists:
        github_client.create_label(
            repo_obj, name=skip_label, color="ededed", description="The title was checked by LLM"
        )
        print(f"Created label '{skip_label}' with description")


def open_issue_event(config, repo_obj, ai_client, github_client):
    print(f"Processing single issue #{config.issue_number} from event trigger")
    try:
        issue = repo_obj.get_issue(config.issue_number)

        if block_user_title_edit(config.event_data, config.skip_label, github_client, issue):
            return []

        issue_processor = IssueProcessor(
            ai_client, github_client, config.prompt, config.skip_label, config.required_labels
        )
        result = issue_processor.process_issue(
            issue=issue,
            auto_update=config.auto_update,
            strip_characters=config.strip_characters,
            quiet=config.quiet,
        )
        return [result]
    except Exception as e:
        print(f"Error processing issue #{config.issue_number}: {e!s}")
        return []


def scan_issue_event(config, repo_obj, ai_client, github_client):
    print("Regular scheduled run - process all recent issues")
    recent_issues = github_client.get_recent_issues(
        repo=repo_obj,
        days_to_scan=config.days_to_scan,
        limit=config.max_issues,
        required_labels=config.required_labels,
        apply_to_closed=config.apply_to_closed,
    )

    if not recent_issues:
        message = f"No open issues found in the last {config.days_to_scan} days"
        if config.required_labels:
            message += f" with the following labels: {', '.join(config.required_labels)}"
        print(message)
        return []

    issue_state = "open and closed" if config.apply_to_closed else "open"
    print(f"Found {len(recent_issues)} `{issue_state}` issues to process")

    issue_processor = IssueProcessor(
        ai_client, github_client, config.prompt, config.skip_label, config.required_labels
    )

    results = []
    for i, issue in enumerate(recent_issues, 1):
        print(f"[{i}/{len(recent_issues)}] Processing issue #{issue.number}")
        result = issue_processor.process_issue(
            issue=issue,
            auto_update=config.auto_update,
            strip_characters=config.strip_characters,
            quiet=config.quiet,
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
        set_verbose(config.verbose)

        ai_client = create_ai_client(
            provider=config.ai_provider, api_key=config.get_api_key(), model_name=config.model_name
        )
        github_client = GitHubClient(config.github_token)

        print(f"Scanning repository: {config.repo_name}")
        repo_obj = github_client.get_repository(config.repo_name)

        pre_process(github_client, repo_obj, config.skip_label)
        if config.is_issue_event and config.issue_number:
            open_issue_event(config, repo_obj, ai_client, github_client)
        else:
            scan_issue_event(config, repo_obj, ai_client, github_client)

    except Exception as error:
        print(f"Error: {error!s}")
        sys.exit(1)


if __name__ == "__main__":
    run()
