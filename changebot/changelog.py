import re

__all__ = ['check_changelog_consistency']


BLOCK_PATTERN = re.compile('\[#.+\]', flags=re.DOTALL)
ISSUE_PATTERN = re.compile('#[0-9]+')


def find_prs_in_changelog(content):
    issue_numbers = []
    for block in BLOCK_PATTERN.finditer(content):
        block_start, block_end = block.start(), block.end()
        block = content[block_start:block_end]
        for m in ISSUE_PATTERN.finditer(block):
            start, end = m.start(), m.end()
            issue_numbers.append(int(block[start:end][1:]))
    return issue_numbers


def find_prs_in_changelog_by_section(content):

    changelog_prs = {}
    version = None
    subcontent = ''
    previous = None

    for line in content.splitlines():
        if '-------' in line:
            if version is not None:
                for pr in find_prs_in_changelog(subcontent):
                    changelog_prs[int(pr)] = version
            version = previous.strip().split('(')[0].strip()
            if 'v' not in version:
                version = 'v' + version
            subcontent = ''
        elif version is not None:
            subcontent += line
        previous = line

    return changelog_prs


def check_changelog_consistency(repo_handler, pr_handler):

    changelog = repo_handler.get_file_contents('CHANGES.rst')

    return review_changelog(pr_handler.number, changelog,
                            pr_handler.milestone, pr_handler.labels)


def review_changelog(pull_request, changelog, milestone, labels):

    issues = []

    if not milestone:
        issues.append("The milestone has not been set")

    sections = find_prs_in_changelog_by_section(changelog)
    changelog_entry = pull_request in sections
    if changelog_entry:
        if not milestone.startswith(sections[pull_request]):
            issues.append("Changelog entry section ({0}) inconsistent "
                          "with milestone ({1})".format(sections[pull_request], milestone))

    if 'no-changelog-entry-needed' in labels:
        if changelog_entry:
            issues.append("Changelog entry present but **no-changelog-entry-needed** label set")
    elif 'Affects-dev' in labels:
        if changelog_entry:
            issues.append("Changelog entry present but **Affects-dev** label set")
    else:
        if not changelog_entry:
            issues.append("Changelog entry not present (or pull request number "
                          "missing) and neither the **Affects-dev** nor the "
                          "**no-changelog-entry-needed** label are set")

    return issues
