import argparse
import csv
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

_first_csv_domain = True


def check_negative_int(value):
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


def create_ascii_table(headers):
    table = PrettyTable(headers)
    table.align = 'l'
    table.max_width = 12
    table.max_width['Title'] = table.max_width['Link'] = 60
    table.align['#User Comments'] = 'r'
    return table


def print_ascii_row(table, row_data, empty_row=None):
    if table is not None:
        table.add_row(row_data)
        if empty_row is not None:
            table.add_row(empty_row)


def write_csv_row(csv_writer, row_data):
    if csv_writer is not None:  # Only write headers if csv writer exists
        csv_writer.writerow(row_data)


def write_csv_headers(domain, headers, **kwargs):
    global _first_csv_domain
    if not _first_csv_domain:
        write_csv_row(kwargs.get('csv_writer'), [])
    write_csv_row(kwargs.get('csv_writer'), [domain + ' issues'])
    write_csv_row(kwargs.get('csv_writer'), headers)
    _first_csv_domain = False


def process_issues(domain, username, issues, **kwargs):
    headers = ['ID', 'Project', 'Title', 'Role', 'Status', '#Comments', 'Link', 'Updated On']
    table = create_ascii_table(headers) if kwargs.get('ascii') else None
    write_csv_headers(domain, headers, **kwargs)

    for issue in issues:
        output_issue(domain, username, issue, table=table, **kwargs)

    if table is not None:
        print(table)


def output_issue(domain, username, issue, table=None, **kwargs):
    user_roles = list(kwargs.get('user_roles', []))
    if issue.fields.reporter.name == username:
        user_roles.append('Reporter')

    link = domain + "/browse/" + issue.key
    updated_time = issue.fields.updated[:10].replace('-', '/')
    comments = [comment for comment in issue.fields.comment.comments if comment.author.name == username]

    row_content = [issue.key, issue.fields.project.name, issue.fields.summary, ','.join(user_roles),
                   issue.fields.status.name, len(comments), link, updated_time]

    # Add to ascii table if enabled
    print_ascii_row(table, row_content, [''] * 8)

    # Write to csv file
    write_csv_row(kwargs.get('csv_writer'), row_content)


def search_jira_domains(domains, username, **kwargs):
    search_field = ','.join(FIELDS)
    search_str = "(assignee = {0} OR reporter = {0})" \
                 "AND (updated >= '{1}' OR created >= '{1}')" \
                 "AND (updated < '{2}' OR created < '{2}')" \
                 "ORDER BY updated {3}".format(username, kwargs.get('start_date', date(1990, 1, 1)),
                                               kwargs.get('end_date', date.today()), kwargs.get('order', 'ASC'))

    for key, domain in domains.items():
        jira = JIRA(domain)
        issues = jira.search_issues(search_str, fields=search_field, maxResults=kwargs.get('jira_limit', 50))

        if issues:
            if kwargs.get('ascii'):
                print("{0} issues".format(key))

            process_issues(domain, username, issues, **kwargs)


def get_program_args():
    parser = argparse.ArgumentParser(description='Returns JIRA issues associated with a given user')
    parser.add_argument('usernames', nargs='+', help='At least one JIRA username must be specified.')

    parser.add_argument('-s', '--startDate', dest='start_date', type=valid_date, default=date(1990, 1, 1),
                        metavar='YYYY-MM-DD', help="The date from which JIRAs are returned.")

    parser.add_argument('-e', '--endDate', dest='end_date', type=valid_date, default=date.today(), metavar='YYYY-MM-DD',
                        help="The date of the most recent JIRA to be returned.")

    parser.add_argument('-d', '--domains', nargs='+', choices=JIRA_LOCATIONS.keys(), default=JIRA_LOCATIONS,
                        help="A list of the JIRA keys associated with the domain(s) that should be searched.")

    parser.add_argument('-jl', '--jira-limit', dest='jira_limit', type=check_negative_int, default=50,
                        help="The maximum number of JIRA issues that will be returned for each domain.")

    parser.add_argument('--lifo', dest='order', action='store_const', const='DESC', default='ASC',
                        help="JIRA issues are output from the most recently updated issue.")

    parser.add_argument('--no-ascii', dest='ascii', action='store_false',
                        help="JIRA issues will not be output to the console.")

    parser.add_argument('-c', '--csv', dest='csv', nargs='?', type=str, choices=csv.list_dialects(), const='excel',
                        help="JIRA issues are output to a csv file 'jira.csv'. This flag takes an optional keyword "
                             "parameter that determines the format of the generated csv file.")

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
    options = {'start_date': a.start_date, 'end_date': a.end_date, 'jira_limit': a.jira_limit, 'order': a.order,
               'user_roles': ['Assignee'], 'ascii': a.ascii}

    for user in a.usernames:
        if a.ascii:
            print("JIRA Issues Associated with {} at domains {}".format(user, list(a.domains)))

        # Only create a file if absolutely necessary
        if a.csv is not None:
            filename = "{}-jira.csv".format(user)
            with open(filename, mode='w') as csvfile:
                options['csv_writer'] = csv.writer(csvfile, dialect=a.csv)
                search_jira_domains(a.domains, user, **options)
        else:
            search_jira_domains(a.domains, user, **options)
