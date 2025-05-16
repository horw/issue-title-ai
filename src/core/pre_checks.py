def block_user_title_edit(event_data, skip_label, github_client, issue):
    if not isinstance(event_data, dict):
        return False
    if event_data["action"] != "edited":
        return False
    if event_data["sender"]["type"] != "User":
        return False

    previous_title = event_data["changes"]["title"]["from"]
    if not previous_title:
        return False
    if skip_label not in [label["name"] for label in event_data["issue"]["labels"]]:
        return False

    github_client.add_issue_comment(
        issue, "This issue has already been processed. Please do not change the title."
    )
    issue.edit(title=previous_title)
    return True
