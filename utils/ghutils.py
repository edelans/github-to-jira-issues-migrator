import migrationauth
import requests
import os

repo = "backend"
org_repo = "waldoapp/" + repo
root_url = "https://api.github.com/repos"
base_url = f"{root_url}/{org_repo}/issues"


def get_repo():
    """Get repo object for current repo specified in org_repo"""

    url = f"{root_url}/{org_repo}"
    return requests.get(
        url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    ).json()


def get_issues_by_label(labels, label_exclusions, pagination=100):
    """Get list of issues by label"""
    assert 0 < pagination <= 100  # pagination size needs to be set properly
    assert labels  # Labels cannot be None

    issues = []
    page = 0
    url = f"{base_url}"

    while True:
        page += 1
        data = {"per_page": pagination, "labels": labels, "page": page}
        response = requests.get(
            url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN), params=data
        )

        if not response.ok:
            print(
                f"* An unexpected response was returned from GitHub: {response} {response.reason}"
            )
            print(response.json())
            exit(1)

        # Get all the issues excluding the PRs and specified labels
        issues.extend(
            [
                issue
                for issue in response.json()
                if not has_label(issue, label_exclusions)
                and not issue.get("pull_request")
            ]
        )

        if not "next" in response.links.keys():
            break

    return issues


def has_label(issue, label_query):
    """Whether an issue has a given label"""

    label_list = label_query.split(",")

    for label_obj in issue["labels"]:
        for label_name in label_list:
            if str(label_obj["name"]) == label_name:
                return True

    return False


def get_single_issue(issue_number):
    """Get specific issue data"""

    url = f"{base_url}/{issue_number}"
    return requests.get(
        url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    ).json()


def close_issue(issue_number):
    """Close issue"""

    url = f"{base_url}/{issue_number}"
    data = {"state": "closed"}
    return requests.patch(
        url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN), json=data
    ).json()


def get_issue_comments(issue):
    """Get comments from given issue dict"""

    comment_url = issue["comments_url"]

    response = requests.get(
        comment_url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    )

    # Omit comments from selected bots
    comments = []
    comments.extend(
        [
            comment
            for comment in response.json()
            if comment["user"]["login"] != "stale[bot]"
            and comment["body"] != "dependency_scan failed."
        ]
    )

    return comments


def add_issue_label(issue_number, label):
    """Add label to given issue"""

    url = f"{base_url}/{issue_number}/labels"

    data = {"labels": [label]}

    response = requests.post(
        url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN), json=data
    )

    return response.json()


def add_issue_comment(issue_number, comment):
    """Add comment to given issue"""

    url = f"{base_url}/{issue_number}/comments"

    data = {"body": comment}

    response = requests.post(
        url, auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN), json=data
    )

    return response.json()


def download_image_with_cookie(image_url, save_dir="images"):
    """Download a private GitHub image using a browser session cookie.
        When accessing the GitHub user-attachments URL from a private repo, I was getting an SSO sign-in request instead of the image because GitHub’s API token is not enough when SSO is enforced.
    As in our case it's just needed for a one-off for a migration, I ended up authenticating my requests with a browser session cookie, and was able to programmatically download the images of the issue.
    """

    os.makedirs(save_dir, exist_ok=True)
    filename = image_url.split("/")[-1] + ".png"
    filepath = os.path.join(save_dir, filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Cookie": migrationauth.GH_SESSION_COOKIE,  # Use browser session cookie
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",  # Correct accept header for images
        "Referer": "https://github.com/",  # Add referer to mimic browser request
    }

    response = requests.get(
        image_url, headers=headers, stream=True, allow_redirects=True
    )

    if response.status_code == 200 and "image" in response.headers.get(
        "Content-Type", ""
    ):
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"✅ Downloaded image: {filepath}")
        return filepath
    else:
        print(f"❌ Failed to download image: {image_url} (Code {response.status_code})")
        return None
