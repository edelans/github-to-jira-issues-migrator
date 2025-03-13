import migrationauth
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import re
import os
import utils.ghutils as ghutils


auth = HTTPBasicAuth(migrationauth.JIRA_EMAIL, migrationauth.JIRA_TOKEN)
root_url = 'https://tricentis.atlassian.net'
base_url = f'{root_url}/rest/api/latest'
html_url = f'{root_url}/browse'
issue_url = f'{base_url}/issue'
project_key = 'WAL'
gh_issue_field = 'customfield_12316846'
data = {
    'projectKeys': project_key
}
headers = {
    'Content-Type': 'application/json',
    "Accept": "application/json",
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
        auth=auth
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
        auth=auth
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
        auth=auth
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
        auth=auth,
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
        json=data,
        auth=auth
    )



def convert_gh_to_jira_markdown(string: str | None) -> (str, list):
    """Convert GitHub Markdown to Jira formatting and download images beforehand."""
    if not string:
        return '', []

    attachments = []  # Store downloaded image paths

    def replace_image(match):
        """Download image and replace with placeholder."""
        alt_text, url = match.groups()
        filepath = ghutils.download_image_with_cookie(url)

        if filepath:
            attachments.append(filepath)
            return f"!{os.path.basename(filepath)}!"  # Temporary placeholder
        return f"[image on GitHub|{url}]"  # If download fails

    # Convert Markdown images and store attachment file paths
    string = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, string)


    # Headers
    string = re.sub(r'(###### )', 'h6. ', string)
    string = re.sub(r'(##### )', 'h5. ', string)
    string = re.sub(r'(#### )', 'h4. ', string)
    string = re.sub(r'(### )', 'h3. ', string)
    string = re.sub(r'(## )', 'h2. ', string)
    string = re.sub(r'(# )', 'h1. ', string)
    # Bold
    string = string.replace('**', '*')
    # Inline code
    string = re.sub(r'`([^`\n]+?)`', r'{{\1}}', string)
    # Code blocks with language
    string = re.sub(
        r'```(\w+)\n(.*?)```',
        lambda m: f"{{code:{m.group(1)}}}{m.group(2)}{{code}}",
        string,
        flags=re.DOTALL
    )
    # Code blocks without language
    string = re.sub(
        r'```(.*?)```',
        r'{code}\1{code}',
        string,
        flags=re.DOTALL
    )
    # Blockquotes
    string = re.sub(
        r'^> (.*)$',
        r'{quote}\1{quote}',
        string,
        flags=re.MULTILINE
    )
    # Unordered lists
    string = re.sub(
        r'^(\s*)[-*] (.*)$',
        lambda m: f"{m.group(1)}* {m.group(2)}",
        string,
        flags=re.MULTILINE
    )
    # Ordered lists
    string = re.sub(
        r'^(\s*)\d+\. (.*)$',
        lambda m: f"{m.group(1)}# {m.group(2)}",
        string,
        flags=re.MULTILINE
    )

    return string, attachments
    

def upload_image_to_jira(issue_key, filepath):
    """Upload an image to JIRA and return the filename."""
    with open(filepath, "rb") as file:
        headers = {'X-Atlassian-Token': 'no-check'}
        response = requests.post(
            f"{issue_url}/{issue_key}/attachments",
            auth=auth,
            headers=headers,
            files={'file': (filepath, file)}
        )

    if response.status_code == 200:
        filename = os.path.basename(filepath)
        print(f"✅ Uploaded image to JIRA: {filename}")
        return filename
    else:
        print(f"❌ Failed to upload image {filepath} (Code {response.status_code})")
        return None


def create_issue(props):
    """Create Jira issue"""
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

    url = issue_url
    issue_type = props['issuetype']
    converted_description, image_paths = convert_gh_to_jira_markdown(props['description'])

    request_data = {
        'fields': {
            'project': {'key': project_key},
            'issuetype': issue_type,
            'components': props['components'],
            'summary': props['summary'],
            'description': converted_description,  # Add converted description
            'reporter': props['reporter'],
            'assignee': props['assignee'],
            'priority': props['priority'],
            'labels': props['labels']
        }
    }

    # Step 3: Create the issue in JIRA
    pprint(request_data)
    response = requests.post(
        url,
        json=request_data,
        headers=headers,
        auth=auth
    )

    if not response.ok:
        print(f"❌ Failed to create issue in JIRA: {response.status_code} {response.reason}")
        print(response.json())
        exit(1)

    issue_key = response.json().get("key")
    print(f"✅ Created JIRA issue: {issue_key}")

    # Step 4: Upload attachments (images)
    if image_paths:
        print("📎 Uploading attachments...")
        for image_path in image_paths:
            upload_image_to_jira(issue_key, image_path)

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
        json=request_data,
        auth=auth
    )


def get_issue_from_url(api_url):
    """Get specific issue data given API URL"""

    return requests.get(
        api_url,
        headers=headers,
        auth=auth
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
        auth=auth,
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
        'body': props['body']
    }

    response = requests.post(
        api_url,
        headers=headers,
        auth=auth,
        json=request_data
    )

    return response.json()
