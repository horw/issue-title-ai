from .verbose import verbose_print


class IssueProcessor:
    def __init__(self, ai_client, github_client, prompt, skip_label, required_labels=None):
        self.ai_client = ai_client
        self.github_client = github_client
        self.prompt = prompt
        self.skip_label = skip_label
        self.required_labels = required_labels

    def process_issue(self, issue, auto_update=False, strip_characters="", quiet=False):
        issue_number = issue.number
        original_title = issue.title
        issue_body = issue.body or ""

        if len(issue_body) < 40:
            print(f"Issue body too short, skipping: {issue_number}, length: {len(issue_body)}")
            comment = (
                "Hello, your description is too short. "
                "This usually means the issue is not fully described, "
                "which can mislead developers. "
                "Please ensure your description is longer than 40 characters."
            )
            self.github_client.add_issue_comment(issue, comment)

            return {
                "issue_number": issue_number,
                "original_title": original_title,
                "improved_title": None,
                "updated": False,
                "skipped": True,
                "reason": "Issue body too short",
            }

        issue_labels = [label.name.lower() for label in issue.labels]
        if self.skip_label in issue_labels:
            print(f"Skipping issue #{issue_number}: Already has '{self.skip_label}' label")
            return {
                "issue_number": issue_number,
                "original_title": original_title,
                "improved_title": None,
                "updated": False,
                "skipped": True,
                "reason": f"Has '{self.skip_label}' label",
            }

        if self.required_labels:
            intersection = set(issue_labels).intersection(set(self.required_labels))
            if not intersection:
                print(
                    f"No matching labels ({self.required_labels}) found in {issue_labels}; issue will not be processed."
                )
                return {
                    "issue_number": issue_number,
                    "original_title": original_title,
                    "improved_title": None,
                    "updated": False,
                    "skipped": True,
                    "reason": f"No matching labels found. Current Issue Labels: '{issue_labels}'; Required Labels: '{self.required_labels}'",
                }

        print(f'Processing issue #{issue_number}: "{original_title}"')

        try:
            improved_title = self.generate_improved_title(original_title, issue_body)
            verbose_print("Model Response: ", improved_title)
            improved_title = improved_title.strip().strip(strip_characters)
            if improved_title == original_title or not improved_title:
                print(f"Title already optimal for issue #{issue_number}")
                return {
                    "issue_number": issue_number,
                    "original_title": original_title,
                    "improved_title": None,
                    "updated": False,
                }

            if auto_update:
                self.github_client.update_issue_title(issue, improved_title)
                if not quiet:
                    comment = (
                        f"🤖 I've improved[^1] the title of this issue "
                        f"for better clarity and discoverability.\n\n"
                        f"**Previous title:** {original_title}\n"
                        f"**New title:** {improved_title}\n\n"
                        "[^1]: Improved by [issue-title-ai](https://github.com/horw/issue-title-ai)"
                    )
                    self.github_client.add_issue_comment(issue, comment)
                    print(f'Updated issue #{issue_number} title to: "{improved_title}"')
            else:
                comment = (
                    f"🤖 I've analyzed[^1] this issue title "
                    f"and have a suggestion for improvement:\n\n"
                    f"**Current title:** {original_title}\n"
                    f"**Suggested title:** {improved_title}\n\n"
                    "[^1]: Suggested by [issue-title-ai](https://github.com/horw/issue-title-ai)"
                )
                self.github_client.add_issue_comment(issue, comment)
                print(f"Added title suggestion to issue #{issue_number}")

            self.github_client.add_issue_label(issue, self.skip_label)
            print(f"Added '{self.skip_label}' label to issue #{issue_number}")
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
        return self.ai_client.generate_content(
            self.prompt.format(original_title=original_title, issue_body=issue_body)
        )
