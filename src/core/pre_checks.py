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
        issue,
        "The title of this issue was changed intentionally. "
        "Please avoid editing it unless you strongly disagree with the modifications. "
        "I only make changes when I'm confident they're necessary. "
        "A well-written title helps programmers and testers better understand the issue's intent, "
        "which leads to more effective and enthusiastic contributions. I appreciate your cooperation.",
    )
    issue.edit(title=previous_title)
    return True
