import utils.ghutils as ghutils
import utils.jirautils as jirautils

jira_product_versions = {}
gh_repo_id = ""


def user_map(gh_username, user_mapping, default_user=""):
    """Return the jira account id from the usermap"""
    assert user_mapping != None  # user_mapping cannot be None

    user = None
    user_id = default_user

    if gh_username in user_mapping:
        user_id = user_mapping[gh_username]

    return {"id": user_id}


def type_map(gh_labels):
    """Return the Jira issue type from a given GitHub label"""

    type_map = {"task": "Task", "bug": "Bug", "user_story": "Story", "Epic": "Epic"}

    for label in gh_labels:
        label_name = str(label["name"])
        if label_name in type_map:
            return type_map[label_name]

    return "Task"


def priority_map(gh_labels):
    """Return the Jira priority from a given GitHub label"""

    priority_map = {
        "blocker (P0)": "Blocker",
        "Priority/P1": "Critical",
        "Priority/P2": "Normal",
        "Priority/P3": "Minor",
    }

    priority = {"name": "Undefined"}

    for label in gh_labels:
        label_name = str(label["name"])
        if label_name in priority_map:
            if priority_map[label_name] != "":
                priority["name"] = priority_map[label_name]
                break

    return priority


def severity_map(gh_labels):
    """Return the Jira severity from a given GitHub label"""

    severity_map = {
        "Severity 1 - Urgent": "Critical",
        "Severity 2 - Major": "Moderate",
        "Severity 3 - Minor": "Low",
    }

    severity = {}

    for label in gh_labels:
        label_name = str(label["name"])
        if label_name in severity_map:
            if severity_map[label_name] != "":
                severity["value"] = severity_map[label_name]
                break

    if "value" in severity:
        return severity

    return None


def status_map(pipeline, issue_type):
    """Return equivalent Jira status for a given ZenHub pipeline"""

    # Untriaged and Backlogs will remain in the state on creation ("New" or "To Do")
    pipeline_map = {
        "In Progress": {"Bug": "ASSIGNED", "Default": "In Progress"},
        "Awaiting Verification": {
            "Bug": "ON_QA",
            "Default": "Review",
            "Epic": "Testing",
        },
        "Epics In Progress": "In Progress",
        "Ready For Playback": {"Bug": "ON_QA", "Epic": "Testing", "Default": "Review"},
        "Awaiting Docs": "In Progress",
        "Closed": "Closed",
    }

    if pipeline in pipeline_map:
        mapping_obj = pipeline_map[pipeline]
        if isinstance(mapping_obj, str):
            return mapping_obj
        if issue_type in mapping_obj:
            return mapping_obj[issue_type]
        if "Default" in mapping_obj:
            return mapping_obj["Default"]

    return None


def issue_map(gh_issue, user_mapping, default_user):
    """Return a dict for Jira to process from a given GitHub issue"""
    assert user_mapping != None  # user_mapping cannot be None

    gh_labels = gh_issue["labels"]

    assignee = None
    contributors = []
    for gh_assignee in gh_issue["assignees"]:
        assignee_id = user_map(gh_assignee["login"], user_mapping)
        if assignee_id:
            if assignee:
                contributors.append(assignee_id)
            else:
                assignee = assignee_id

    # Make sure a string is returned for the issue body
    issue_body = ""
    if gh_issue["body"]:
        issue_body = gh_issue["body"]

    issue_title = gh_issue["title"]
    issue_type = type_map(gh_labels)

    # Fetch repo ID if not already populated
    global gh_repo_id
    if gh_repo_id == "":
        gh_repo_id = str(ghutils.get_repo()["id"])

    # Handle labels
    labels = []
    for label in gh_labels:
        label_name = str(label["name"])
        labels.append(label_name.replace(" ", "_"))

    issue_mapping = {
        "issuetype": {"name": issue_type},
        "components": [{"name": ghutils.repo}],
        "summary": issue_title,
        "description": issue_body,
        "reporter": user_map(gh_issue["user"]["login"], user_mapping, default_user),
        "assignee": assignee,
        "priority": priority_map(gh_labels),
        "labels": labels,
        jirautils.gh_issue_field: gh_issue["html_url"],
    }

    return issue_mapping


def comment_map(gh_comment):
    """Return a dict for Jira to process from a given GitHub comment"""

    gh_user = gh_comment["user"]["login"]
    converted_description, image_paths = jirautils.convert_gh_to_jira_markdown(
        gh_comment["body"]
    )

    return {
        "body": f'{gh_comment["created_at"]} @{gh_user}\n{converted_description}'
    }, image_paths
