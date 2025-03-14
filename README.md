# GitHub to Jira Migration

A tool to migrate your Github issues into Jira issues, as [demonstrated with this example](https://github.com/edelans/github-to-jira-issues-migrator/issues/1).

![Image](https://github.com/user-attachments/assets/3004900d-4711-4957-82d8-79451d71ca50)

This project is a fork from https://github.com/dhaiducek/github-to-jira-migration, itself largely inspired by the blog
[How to migrate GitHub issues to Jira](https://zmcddn.github.io/how-to-migrate-github-issues-to-jira.html) by
[@zmcddn](https://github.com/zmcddn).
This fork is independent of the original project and is not affiliated with or endorsed by its original authors. It includes additional improvements and a migration service for those who prefer a hassle-free solution.

Notable Changes:

- Updated authentication (original method didn’t work for me).
- User references now use account IDs (instead of usernames/emails, for GDPR-compliant Jira instances).
- GitHub markdown converted to Jira formatting (headings, links, bold, italic, etc.).
- Image re-upload support for private repositories protected by SSO (this was tricky!).
- Removed unnecessary features (Zenhub integration, label-based priority/component management, etc.).
- Formatted code using blake for consistency.
- for the full details, go to the commit history!

Example of fomratting:
![Image](https://github.com/user-attachments/assets/d695cd17-c813-41ef-b1e0-781cef715a6e)

It worked for a migration in March 2025. Feel free to adapt it to your usecase! **...and if you'd rather have your devs focus on what matters (your roadmap!) and pay a few hundred dollars to have this migration handled for you, jump to the end of this page!!**

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
✅ A seamless transition so your devs can focus on what matters

📩 Interested? Contact me here: [Migration Request Form](https://docs.google.com/forms/d/e/1FAIpQLSdF-CFw37gvnL2e2-IYMq3gTLhsLsMNbTGL_B_pv5lkftTDDA/viewform?usp=header), and let's make it happen! 🚀
