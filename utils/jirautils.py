import migrationauth
import requests

root_url = 'https://tricentis.atlassian.net'
base_url = f'{root_url}/rest/api/latest'
html_url = f'{root_url}/browse'
issue_url = f'{base_url}/issue'
project_key = 'WAL'
security_level = 'Tricentis Employee'  # To be safe, restrict to RH Employees
gh_issue_field = 'customfield_12316846'
data = {
    'projectKeys': project_key
}
headers = {
    'Authorization': f'Bearer {migrationauth.JIRA_TOKEN}',
    'Content-Type': 'application/json',
}


def get_user(user_query):
    """Get user object from query (username, name, or e-mail)"""

    url = f'{base_url}/user'
    data = {
        'accountId': user_query
    }

    response = requests.get(
        url,
        headers=headers,
        params=data,
    )

    if not response.ok:
        print(
            f"An unexpected response was returned from Jira while trying to get user {user_query}: {response} {response.reason}")
        exit(1)

    return response.json()


def get_issue_types():
    """Get types of issues from Jira"""

    url = f'{issue_url}/createmeta'

    response = requests.get(
        url,
        headers=headers,
        params=data,
    )

    return response.json()['projects'][0]['issuetypes']


def get_issue_meta(issue_type_name):
    """Get meta fields for an issue type"""

    request_data = data
    request_data['issuetypeNames'] = issue_type_name
    request_data['expand'] = 'projects.issuetypes.fields'

    url = f'{issue_url}/createmeta'

    response = requests.get(
        url,
        headers=headers,
        params=request_data,
    )

    return response.json()['projects'][0]['issuetypes'][0]


def get_transitions(issue_key):
    """Get available transitions for an issue"""

    url = f'{issue_url}/{issue_key}/transitions'
    data = {
        'expand': 'transitions.fields'
    }

    return requests.get(
        url,
        headers=headers,
        json=data
    ).json()


def do_transition(issue_key, target_status_name):
    """Execute a transition for an issue"""

    target_status = None
    transition_response = get_transitions(issue_key)
    for transition in transition_response['transitions']:
        if target_status_name == transition['name']:
            target_status = {'id': transition['id']}

    url = f'{issue_url}/{issue_key}/transitions'
    data = {
        'transition': target_status
    }

    return requests.post(
        url,
        headers=headers,
        json=data
    )


def create_issue(props):
    """Create Jira issue"""
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

    url = issue_url
    issue_type = props['issuetype']
    request_data = {
        'project': {
            'key': project_key
        },
        'security': {
            'name': security_level
        },
        'issuetype': issue_type,
        'components': props['components'],
        'summary': props['summary'],
        'description': props['description'],
        'reporter': props['reporter'],
        'assignee': props['assignee'],
        'priority': props['priority'],
        'labels': props['labels'],

        # Custom "GitHub Issue" field
        # gh_issue_field: props[gh_issue_field]
    }

    response = requests.post(
        url,
        json={'fields': request_data},
        headers=headers,
    )

    if not response.ok:
        print(
            f'* An unexpected response was returned from Jira during issue creation: {response} {response.reason}')
        print(response.json())
        exit(1)

    return response.json()


def update_issue(issue_key, data):
    """Update existing Jira issue"""

    url = f'{issue_url}/{issue_key}'

    request_data = {
        'update': {},
        'fields': data
    }

    return requests.put(
        url,
        headers=headers,
        json=request_data
    )


def get_issue_from_url(api_url):
    """Get specific issue data given API URL"""

    return requests.get(
        api_url,
        headers=headers,
    )


def get_single_issue(issue_key):
    """Get specific issue data"""

    url = f'{issue_url}/{issue_key}'

    response = get_issue_from_url(url)

    return response.json()


def search_issues(jql_query):
    """Get issues based on JQL query"""
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-post

    url = f'{base_url}/search'

    return requests.post(
        url,
        headers=headers,
        json={
            'jql': jql_query,
            # 'fields': ['status']
        }
    ).json()


def add_comment(issue_key, props):
    """Add comment given issue key and props"""

    api_url = f'{issue_url}/{issue_key}/comment'

    return add_comment_from_url(api_url, props)


def add_comment_from_url(api_url, props):
    """Add comment given API URL and props"""

    request_data = {
        'visibility': {
            'type': 'group',
            'value': security_level
        },
        'body': props['body']
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=request_data
    )

    return response.json()
