import migrationauth
import requests
import os
import re

repo = 'Product-Design'
org_repo = 'waldoapp/'+ repo
root_url = 'https://api.github.com/repos'
base_url = f'{root_url}/{org_repo}/issues'


def get_repo():
    """Get repo object for current repo specified in org_repo"""

    url = f'{root_url}/{org_repo}'
    return requests.get(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    ).json()


def get_issues_by_label(labels, label_exclusions, pagination=100):
    """Get list of issues by label"""
    assert 0 < pagination <= 100  # pagination size needs to be set properly
    assert labels                 # Labels cannot be None

    issues = []
    page = 0
    url = f'{base_url}'

    while True:
        page += 1
        data = {
            'per_page': pagination,
            'labels': labels,
            'page': page
        }
        response = requests.get(
            url,
            auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
            params=data
        )

        if not response.ok:
            print(
                f'* An unexpected response was returned from GitHub: {response} {response.reason}')
            print(response.json())
            exit(1)

        # Get all the issues excluding the PRs and specified labels
        issues.extend([issue for issue in response.json()
                       if not has_label(issue, label_exclusions) and not issue.get("pull_request")])

        if not 'next' in response.links.keys():
            break

    return issues


def has_label(issue, label_query):
    """Whether an issue has a given label"""

    label_list = label_query.split(',')

    for label_obj in issue['labels']:
        for label_name in label_list:
            if str(label_obj['name']) == label_name:
                return True

    return False


def get_single_issue(issue_number):
    """Get specific issue data"""

    url = f'{base_url}/{issue_number}'
    return requests.get(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    ).json()


def close_issue(issue_number):
    """Close issue"""

    url = f'{base_url}/{issue_number}'
    data = {
        'state': 'closed'
    }
    return requests.patch(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    ).json()


def get_issue_comments(issue):
    """Get comments from given issue dict"""

    comment_url = issue['comments_url']

    response = requests.get(
        comment_url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    )

    # Omit comments from selected bots
    comments = []
    comments.extend([comment for comment in response.json()
                    if comment['user']['login'] != 'stale[bot]' and comment['body'] != 'dependency_scan failed.'])

    return comments


def add_issue_label(issue_number, label):
    """Add label to given issue"""

    url = f'{base_url}/{issue_number}/labels'

    data = {
        'labels': [label]
    }

    response = requests.post(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    )

    return response.json()


def add_issue_comment(issue_number, comment):
    """Add comment to given issue"""

    url = f'{base_url}/{issue_number}/comments'

    data = {
        'body': comment
    }

    response = requests.post(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    )

    return response.json()


def get_real_image_url(issue_number, image_url):
    """Fetch the GitHub issue and extract the correct image URL."""
    url = f"{base_url}/{issue_number}"  # GitHub API issue endpoint
    headers = {
        "Authorization": f"token {migrationauth.GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Issue-Migrator"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issue_data = response.json()
        
        # Check if the correct image URL exists in the API response
        for comment in issue_data.get("comments", []):
            if image_url in comment.get("body", ""):
                return image_url  # Use the provided URL if it's directly referenced

    print(f"⚠️ No direct API image URL found for {image_url}")
    return None  # Prevent download attempt

def download_image_from_github(issue_number, image_url, save_dir="images"):
    """Download an image from GitHub API if it's a private attachment."""
    
    os.makedirs(save_dir, exist_ok=True)
    filename = image_url.split("/")[-1]
    filepath = os.path.join(save_dir, filename)

    real_image_url = get_real_image_url(issue_number, image_url)
    if not real_image_url:
        print(f"❌ No valid download URL found for image: {image_url}")
        return None

    headers = {
        "Authorization": f"token {migrationauth.GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Issue-Migrator"
    }

    response = requests.get(real_image_url, headers=headers, stream=True, allow_redirects=True)

    # If response is HTML, it's an authentication page, not an image
    if "text/html" in response.headers.get("Content-Type", ""):
        print(f"⚠️ Still receiving an authentication page for {image_url}. Check SSO settings.")
        return None

    if response.status_code == 200:
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"✅ Downloaded image: {filepath}")
        return filepath
    else:
        print(f"❌ Failed to download image: {image_url} (Code {response.status_code})")
        return None
    

def extract_issue_number(url: str) -> int | None:
    """Extract the issue number from a GitHub issue URL."""
    match = re.search(r'/issues/(\d+)$', url)
    return int(match.group(1)) if match else None