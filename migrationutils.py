import ghutils
import jirautils


def user_map(gh_username, user_mappings, default_user=''):
    """Return the user e-mail from the usermap"""
    assert user_mappings  # user_mappings cannot be None

    user = None
    user_email = default_user

    if gh_username in user_mappings:
        user_email = user_mappings[gh_username]

    if user_email != '':
        user = {'name': jirautils.get_user(user_email)[0]['name']}

    return user


def component_map(gh_labels):
    """Return the Jira components from a given GitHub label"""

    component_map = {
        'squad:policy-grc': 'GRC',
        'squad:doc': 'Documentation'
    }

    components = []
    component_count = 0
    for label in gh_labels:
        label_name = str(label['name'])
        if label_name.startswith('squad:'):
            component_count += 1
            if label_name in component_map:
                components.append({'name': component_map[label_name]})

    return components, component_count


def type_map(gh_labels):
    """Return the Jira issue type from a given GitHub label"""

    type_map = {
        'task': 'Task',
        'bug': 'Bug',
        'user_story': 'Story',
        'Epic': 'Epic'
    }

    for label in gh_labels:
        label_name = str(label['name'])
        if label_name in type_map:
            return type_map[label_name]

    return 'Task'


def priority_map(gh_labels):
    """Return the Jira priority from a given GitHub label"""

    priority_map = {
        'blocker (P0)': 'Blocker',
        'Priority/P1': 'Critical',
        'Priority/P2': 'Major',
        'Priority/P3': 'Normal',
        'Severity 1 - Urgent': 'Critical',
        'Severity 2 - Major': 'Major',
        'Severity 3 - Minor': 'Normal',
    }

    priority = {
        'name': 'Undefined'
    }

    for label in gh_labels:
        label_name = str(label['name'])
        if label_name in priority_map:
            if priority_map[label_name] != '':
                priority['name'] = priority_map[label_name]
                break

    return priority


def should_close(gh_issue):
    """Return the whether an issue has a label signaling it should not be closed"""

    no_close_labels = 'bugzilla,canary-failure'

    return ghutils.has_label(gh_issue, no_close_labels)


def issue_map(gh_issue, user_mappings, default_user):
    """Return a dict for Jira to process from a given GitHub issue"""
    assert user_mappings  # user_mappings cannot be None

    gh_labels = gh_issue['labels']

    # Flag for whether the GitHub issue can be closed after migration
    # Don't close the issue if:
    # - It's connected to Bugzilla
    # - It's a multi-squad issue
    can_close = True
    components, component_count = component_map(gh_labels)
    if component_count > 1 or should_close(gh_issue):
        can_close = False

    gh_assignee = ''
    if gh_issue['assignee']:
        gh_assignee = gh_issue['assignee']['login']

    return {
        'issuetype': {
            'name': type_map(gh_labels)
        },
        'components': components,
        'summary': gh_issue['title'],
        'description': gh_issue['body'],
        'reporter': user_map(gh_issue['user']['login'], user_mappings, default_user),
        'assignee': user_map(gh_assignee, user_mappings),
        # 'status': '', <-- This would need to be pulled from ZenHub's Pipeline field
        'priority': priority_map(gh_labels),
        # 'version': '', -- This would need to be pulled from ZenHub's Release field
        # Custom "GitHub Issue" field
        jirautils.gh_issue_field: gh_issue['html_url']
    }, can_close


def comment_map(gh_comment, user_mappings):
    """Return a dict for Jira to process from a given GitHub comment"""
    assert user_mappings  # user_mappings cannot be None

    gh_user = gh_comment['user']['login']

    # A default user isn't required here because it's inferred from the token
    return {
        'author': user_map(gh_user, user_mappings),
        'body': f'{gh_comment["created_at"]} @{gh_user}\n{gh_comment["body"]}'
    }
