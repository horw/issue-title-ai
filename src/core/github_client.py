import datetime

from github import Github, Auth


class GitHubClient:
    def __init__(self, token):
        if not token:
            raise ValueError("GitHub token not provided")
        self.client = Github(auth=Auth.Token(token))

    def get_repository(self, repo_name):
        try:
            return self.client.get_repo(repo_name)
        except Exception as e:
            print(f"Error accessing repository {repo_name}: {e!s}")
            raise

    def get_recent_issues(
        self, repo, days_to_scan=7, limit=100, required_labels=None, apply_to_closed=False
    ):
        date_threshold = datetime.datetime.now() - datetime.timedelta(days=days_to_scan)

        try:
            state = "all" if apply_to_closed else "open"

            all_issues = repo.get_issues(
                state=state,
                sort="created",
                direction="desc",
                labels=required_labels if required_labels else None,
            )

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
