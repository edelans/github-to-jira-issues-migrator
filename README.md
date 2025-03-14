# GitHub to Jira Migration

This project was forked from https://github.com/dhaiducek/github-to-jira-migration, itself argely inspired by the blog
[How to migrate GitHub issues to Jira](https://zmcddn.github.io/how-to-migrate-github-issues-to-jira.html) by
[@zmcddn](https://github.com/zmcddn).

Here are the main things I changed to make it work for my usecase: (migrate mulitple private repos, keep formatting)

- update authentication
- use accountIDs to reference users because username/emails didn't work with my JIRA instance, configured in GDPR strict mode
- handle jira markdown in issue description and comments (links, h1, h2, bold, italic etc...)
- handle image re-upload (this one was tricky)
- simplify things I didn't use (remove zenhub, priority and component management...)
- use blake for formatting

It worked for a March 2025 migration. Feel free to adapt it to your usecase!
**Would you rather focus on what matters and pay a few hundred $ to have this migration handled for you? Jump to the end of this page!**

## Prerequisites

1. Install Python dependencies:

   ```shell
   python3 -m pip install requests argparse
   ```

2. Rename and populate the following template files:

   - [`migrationutils.py`](migrationauth_template.py) - Authentication variables for GitHub and Jira
   - [`config.json`](config_template.json) - Configuration for GitHub issue label filtering (A `config.json` can be
     renamed to `config\_\*.json` if you want to reserve unused configs for later but not track them in Git.)
   - [`user_map.json`](user_map_template.json) - Mapping of GitHub users to Jira users (this can alternatively be
     supplied using the `user_map` key in `config.json` or not supplied at all if user mapping is not desired.)

## Running the migration script

Invoke the script using the Python CLI. Use arguments to override the `config.json` file, display verbose logging, or
run a dry run:

**NOTE**: Running with `--dry-run` and/or `--dry-run -v` prior to migration is highly recommended. While the output is
long, you'll be able to verify data that is being passed to Jira.

```
$ python3 jira-migration.py --help

usage: jira-migration.py [-h] [-l LABEL_FILTER] [-e LABEL_EXCLUSIONS]
                         [-c COMPLETION_LABEL] [-v] [--dry-run]

Utility to migrate issues from GitHub to Jira

options:
  -h, --help            show this help message and exit
  -l LABEL_FILTER, --label-filter LABEL_FILTER
                        Filter issues by GitHub label (comma separated list)
  -e LABEL_EXCLUSIONS, --label-exclusions LABEL_EXCLUSIONS
                        Exclude issues by GitHub label (comma separated list)
  -c COMPLETION_LABEL, --completion-label COMPLETION_LABEL
                        Label to filter/add for issues that have been migrated
  -v, --verbose         Print additional logs for debugging
  --dry-run             Only run get operations and don't update/create issues
```

## Adapting for other use cases

These scripts use some specific label filtering for my use cases. Here are some pointers if you're modifying for a
different use case:

- Update `root_url` in [`jirautils.py`](utils/jirautils.py)
- Update `project_key`, `security_level`, and custom fields in [`jirautils.py`](utils/jirautils.py)
- Update `org_repo` in [`ghutils.py`](utils/ghutils.py)
- Look at the mapping flows in [`migrationutils.py`](utils/migrationutils.py) (to adapt it to your own usage of github and JIRA)

## Resources

- [GitHub API](https://docs.github.com/en/rest)
- [Jira API](https://docs.atlassian.com/software/jira/docs/api/REST/latest)

# 💡 Want a hassle-free migration?

Skip the setup : I offer a done-for-you migration service for a few hundred dollars (depending on customization needs). You'll get:

✅ A fully managed migration, tailored to your use case
✅ A simple credit card payment link + invoice for easy expensing (no procurement delays or headaches)
✅ A seamless transition so you can focus on what matters

📩 Interested? Contact me here: [Migration Request Form](https://docs.google.com/forms/d/e/1FAIpQLSdF-CFw37gvnL2e2-IYMq3gTLhsLsMNbTGL_B_pv5lkftTDDA/viewform?usp=header), and let's make it happen! 🚀
