import argparse
from collections import OrderedDict
from datetime import date, datetime
from jira import JIRA
from prettytable import PrettyTable

JIRA_LOCATIONS = OrderedDict([
    ('JBOSS', 'https://issues.jboss.org'),
    ('HIBERNATE', 'https://hibernate.atlassian.net'),
    # ('APACHE', 'https://issues.apache.org')
])
FIELDS = ['project', 'summary', 'key', 'status', 'reporter', 'assignee', 'updated', 'comment']


def check_negative(value):
    try:
        ret_value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid input '{}', --jira-limit parameter must be a valid integer")

    if ret_value < 1:
        raise argparse.ArgumentTypeError("invalid input '{}', --jira-limit parameter must be > 0".format(value))
    return ret_value


def valid_date(string):
    try:
        return datetime.strptime(string, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Not a valid date: '{0}'.".format(string))


def print_issues(domain, username, issues, roles=list()):
    table = PrettyTable(['ID', 'Project', 'Title', 'Role', 'Status', '#Comments', 'Link', 'Updated On'])
    table.align = 'l'
    table.max_width = 12
    table.max_width['Title'] = table.max_width['Link'] = 60
    table.align['#User Comments'] = 'r'
    for issue in issues:
        add_issue_to_table(domain, username, table, issue, list(roles))
    print(table)


def add_issue_to_table(domain, username, table, issue, roles=list()):
    if issue.fields.reporter.name == username:
        roles.append('Reporter')
    link = domain + "/browse/" + issue.key
    updated_time = issue.fields.updated[:10].replace('-', '/')
    comments = [comment for comment in issue.fields.comment.comments if comment.author.name == username]
    table.add_row([issue.key, issue.fields.project.name, issue.fields.summary,
                   ','.join(roles), issue.fields.status.name, len(comments), link, updated_time])
    table.add_row([''] * 8)


def search_all_issues(jira_dict, username, start_date=date(1990, 1, 1), end_date=date.today(), max_results=50):
    for key, domain in jira_dict.items():
        jira = JIRA(domain)
        issues = jira.search_issues("(assignee = {0} OR reporter = {0})"
                                    "AND (updated >= '{1}' OR created >= '{1}')"
                                    "AND (updated < '{2}' OR created < '{2}')"
                                    "ORDER BY updated ASC"
                                    .format(username, start_date, end_date),
                                    fields=','.join(FIELDS),
                                    maxResults=max_results)
        if issues:
            print("{0} JIRA issues involving '{1}'".format(key, username))
            print_issues(domain, username, issues, roles=['Assignee'])


def get_program_args():
    parser = argparse.ArgumentParser(description='Returns JIRA issues associated with a given user')
    parser.add_argument('username', type=str, help='A JIRA <username> must be specified')

    parser.add_argument('-s', '--startDate', dest='start_date', type=valid_date, default=date(1990, 1, 1),
                        metavar='YYYY-MM-DD', help="The date from which JIRAs are returned.")

    parser.add_argument('-e', '--endDate', dest='end_date', type=valid_date, default=date.today(), metavar='YYYY-MM-DD',
                        help="The date of the most recent JIRA to be returned.")

    parser.add_argument('-d', '--domains', nargs='+', choices=JIRA_LOCATIONS.keys(), default=JIRA_LOCATIONS,
                        help="A list of the JIRA keys associated with the domain(s) that should be searched.")

    parser.add_argument('-jl', '--jira-limit', dest='jira_limit', type=check_negative, default=50,
                        help="The maximum number of JIRA issues that will be returned for each domain.")

    args = parser.parse_args()

    # Convert list of domain keys into OrderedDict
    if isinstance(args.domains, list):
        domains = OrderedDict()
        for domain_key in args.domains:
            domains[domain_key] = JIRA_LOCATIONS[domain_key]
        args.domains = domains

    return args


if __name__ == '__main__':
    a = get_program_args()
    search_all_issues(a.domains, a.username, a.start_date, a.end_date, a.jira_limit)
