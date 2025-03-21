import utils.ghutils as ghutils
import utils.jirautils as jirautils
import utils.migrationutils as migrationutils
import json
from pprint import pprint
import argparse

try:
    config_file = open("config.json")
    config_json = json.load(config_file)
    config_file.close()
except:
    print(
        "* Error: config.json not found. Please populate the configuration file before continuing."
    )
    exit(1)

user_map_json = None
try:
    user_map_file = open("user_map.json")
    user_map_json = json.load(user_map_file)
    user_map_file.close()
except:
    print(
        "* Warning: user_map.json not found. This may be ignored if user_map is supplied in config.json or isn't used."
    )

user_map = {}
if config_json:
    if user_map_json:
        user_map = user_map_json
    elif "user_map" in config_json:
        user_map = config_json["user_map"]
    if "default_jira_user" in config_json:
        default_user = config_json["default_jira_user"]
    else:
        print(
            "Error finding default Jira user. This is required for creating Jira issues."
        )
        exit(1)
else:
    print("Error loading config.json.")
    exit(1)

label_filter = ""
label_exclusions = ""
completion_label = ""

# Parse config file
if "label_filter" in config_json:
    label_filter = config_json["label_filter"]
if "label_exclusions" in config_json:
    label_exclusions = config_json["label_exclusions"]
if "completion_label" in config_json:
    completion_label = config_json["completion_label"]

# Parse CLI arguments (these override the config file)
description = "Utility to migrate issues from GitHub to Jira"
parser = argparse.ArgumentParser(description=description)
parser.add_argument(
    "-l", "--label-filter", help="Filter issues by GitHub label (comma separated list)"
)
parser.add_argument(
    "-e",
    "--label-exclusions",
    help="Exclude issues by GitHub label (comma separated list)",
)
parser.add_argument(
    "-c",
    "--completion-label",
    help="Label to filter/add for issues that have been migrated",
)
parser.add_argument(
    "-s",
    "--squad-completion-label",
    help="Label to filter/add for issues that have been migrated for non-closeable issues",
)
parser.add_argument(
    "-v",
    "--verbose",
    default=False,
    action="store_true",
    help="Print additional logs for debugging",
)
parser.add_argument(
    "--dry-run",
    default=False,
    action="store_true",
    help="Only run get operations and don't update/create issues",
)
args = parser.parse_args()

if args.label_filter:
    label_filter = args.label_filter
if args.label_exclusions:
    label_exclusions = args.label_exclusions
if args.completion_label:
    completion_label = args.completion_label

# Collect GitHub issues using query config or CLI
label_exclusions = f"{completion_label},{label_exclusions}"
gh_issues = ghutils.get_issues_by_label(label_filter, label_exclusions)
print(f"* Recovered {len(gh_issues)} issues to be migrated")

jira_mappings = []

if len(gh_issues) == 0:
    print("* No issues were returned from GitHub:")
    print(f"  Label filter:     {label_filter}")
    print(f"  Label exclusions: {label_exclusions}")


# ugly hack to be able to upload to jira images downloaded from gh comments.
jira_comment_image_paths = []

# Iterate over GitHub issues and collect mapping objects
for gh_issue in gh_issues:
    if args.verbose:
        pprint(gh_issue)
    gh_url = gh_issue["html_url"]
    print(f'* Creating Jira mapping for {gh_url} ({gh_issue["title"]})')

    jira_issue_input = migrationutils.issue_map(gh_issue, user_map, default_user)

    # Collect comments from the GitHub issue
    # TODO: refacto image management
    gh_comments = ghutils.get_issue_comments(gh_issue)
    jira_comment_input = []
    for comment in gh_comments:
        comment_object, image_paths = migrationutils.comment_map(comment)
        jira_comment_input.append(comment_object)
        jira_comment_image_paths += image_paths

    # Store issue mapping objects
    mapping_obj = {
        "gh_issue_number": gh_issue["number"],
        "gh_issue_url": gh_url,
        "issue": jira_issue_input,
        "comments": jira_comment_input,
    }
    jira_mappings.append(mapping_obj)

    if args.verbose:
        pprint(mapping_obj)

# Iterate over Jira mappings to create issues with comments
issue_failures = []
duplicate_issues = {}
for jira_map in jira_mappings:

    gh_issue_url = jira_map["issue"][jirautils.gh_issue_field]
    gh_issue_title = jira_map["issue"]["summary"]
    # print(
    #     '* Checking for issues already linked to GitHub issue ' +
    #     f'{gh_issue_url} ({gh_issue_title})')

    # custom_field_index = jirautils.gh_issue_field.split('_')[1]
    # custom_field = f'cf[{custom_field_index}]'
    # duplicate_list = jirautils.search_issues(
    #     f'{custom_field} = "{gh_issue_url}"')['issues']
    # if len(duplicate_list) > 0:
    #     duplicate_issues[gh_issue_url] = list(
    #         map(lambda issue: issue['key'], duplicate_list))

    print(f"* Creating Jira issue for {gh_issue_url} ({gh_issue_title})")

    jira_api_url = ""
    jira_key = ""
    backlink = (
        f"\n\n---\nℹ️  This issue was migrated from GitHub issue {gh_issue_url}\n---"
    )
    jira_map["issue"]["description"] += backlink

    if args.verbose:
        print("jira_map just before issue creation: ")
        pprint(jira_map)

    if not args.dry_run:
        create_response = jirautils.create_issue(jira_map["issue"])

        if args.verbose:
            pprint(create_response)
        if "self" in create_response:
            jira_api_url = create_response["self"]
        if "key" in create_response:
            jira_key = create_response["key"]

    if not args.dry_run and jira_key == "":
        print("* Error: A Jira key was not returned in the creation response")
        issue_failures.append(gh_issue_url)
        continue

    print(f"  * Adding comments from GitHub to new Jira issue {jira_key}")
    if not args.dry_run:
        if jira_comment_image_paths:
            print("📎 Uploading attachments...")
            for image_path in jira_comment_image_paths:
                jirautils.upload_image_to_jira(jira_key, image_path)
        for comment_map in jira_map["comments"]:
            if args.verbose:
                print(comment_map)
            comment_response = jirautils.add_comment_from_url(
                f"{jira_api_url}/comment", comment_map
            )
            if args.verbose:
                pprint(comment_response)

    # if not args.dry_run:
    #     if jira_map['issue']['status']:
    #         transition_response = jirautils.do_transition(
    #             jira_key, jira_map['issue']['status'])
    #         if args.verbose:
    #             pprint(transition_response)

    # Add comment in GH issue with link to new Jira issue
    gh_issue_number = jira_map["gh_issue_number"]
    jira_html_url = f"{jirautils.html_url}/{jira_key}"
    gh_comment = f"This issue has been migrated to Jira: {jira_html_url}"

    if not args.dry_run:
        comment_response = ghutils.add_issue_comment(gh_issue_number, gh_comment)
        print("  * Migration comment added to the gh issue")
        if args.verbose:
            pprint(comment_response)

    # Add migration label if allowed
    print("  * Handling GitHub issue labels and closing issue if allowed")
    if not args.dry_run:
        label_response = ghutils.add_issue_label(gh_issue_number, completion_label)
        if args.verbose:
            pprint(label_response)

if len(issue_failures) > 0:
    print("* Failed to create Jira issues for:")
    for issue in issue_failures:
        print(f"  {issue}")

if len(duplicate_issues) > 0:
    print("* Duplicate issues detected for review:")
    for issue in duplicate_issues:
        print(f"  {issue}: {duplicate_issues[issue]}")
