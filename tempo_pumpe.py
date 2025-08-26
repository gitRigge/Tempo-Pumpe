import argparse
import logging
import os
import sys
from datetime import datetime

import yaml
from atlassian import Jira
from dotenv import load_dotenv
from tempoapiclient import client_v4


def calculate_seconds(hours: float):
    """
    Converts a time duration from hours to seconds.

    Args:
        hours (float): The number of hours to convert.

    Returns:
        int: The equivalent duration in seconds.
    """
    return int(hours*60*60)


def calculate_hours(seconds: int):
    """
    Converts a duration from seconds to hours.

    Args:
        seconds (int): The duration in seconds.

    Returns:
        float: The equivalent duration in hours.
    """
    return float(seconds/60/60)


def get_issues():
    """
    Reads issue keys from a YAML file and returns them along with a mapping of
    issue values to their keys.

    Returns:
        tuple: A tuple containing:
            - keys (dict): The dictionary loaded from the '.issues.yml' file.
            - ids (dict): A dictionary mapping each value in 'keys' to its
              corresponding key.
    """
    ids = {}
    with open('.issues.yml', 'r') as file:
        keys = yaml.safe_load(file)
    for i in keys:
        ids[keys[i]] = i
    return keys, ids


def set_issues(issue_key: str, issue_id: int, summary: str):
    """
    Appends issue information to the '.issues.yml' file.

    Args:
        issue_key (str): The key or identifier for the issue.
        issue_id (int): The numeric ID of the issue.
        summary (str): A brief summary or description of the issue.

    The function writes the issue details in the format:
        <issue_key>: <issue_id> # <summary>
    to the '.issues.yml' file, creating a new entry for each call.
    """
    with open('.issues.yml', 'a') as file:
        file.write('\n{}: {} # {}'.format(issue_key, issue_id, summary))


def get_issue_id(issue_key: str):
    """
    Retrieves the numeric ID of a JIRA issue given its issue key.

    If the issue key is not already cached, fetches the issue details from
    JIRA using the REST API, caches the issue ID and summary, and returns the
    issue ID. If the issue key is already cached, returns the cached issue ID.

    Args:
        issue_key (str): The key of the JIRA issue (e.g., "PROJ-123").

    Returns:
        int: The numeric ID of the JIRA issue, or -1 if retrieval fails.

    Raises:
        Exception: If an unexpected error occurs during issue retrieval.
    """
    global issue_keys, issue_ids
    if issue_key not in issue_keys:
        # JIRA Rest Client
        jira = Jira(
            url=os.getenv("JIRA_BASE_URL"),
            username=os.getenv("JIRA_USER"),
            password=os.getenv("JIRA_TOKEN"),
            cloud=True
        )
        # API Call
        try:
            issue = jira.issue(key=issue_key, fields='id,summary')
            issue_id = int(issue['id'])
            summary = issue['fields']['summary']
            set_issues(issue_key, issue_id, summary)
            issue_keys[issue_key] = issue_id
            issue_ids[issue_id] = issue_key
            return issue_id
        except (KeyError, TypeError, AttributeError) as e:
            logging.error(f"Error retrieving issue {issue_key}: {e}")
            return -1
        except Exception as e:
            logging.error(
                f"Unexpected error retrieving issue {issue_key}: {e}"
            )
            raise
    else:
        return int(issue_keys[issue_key])


load_dotenv()

logging.basicConfig(
    filename=r'logs\worklog_pumpe.log',
    format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s',
    encoding='utf-8',
    level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument(
    '-w', '--worklogs', help='Path to worklogs file', required=True)
args = parser.parse_args()

# Tempo REST Client
tempo = client_v4.Tempo(
    auth_token=os.getenv("TEMPO_TOKEN"),
    base_url=os.getenv("TEMPO_BASE_URL")
)

# Recent issues
issue_keys, issue_ids = get_issues()

# Worklogs
with open(args.worklogs, 'r') as file:
    content = yaml.safe_load(file)

imports_ok = False
most_recent_logs = ''

if len(content):
    logged = {}
    for i in content:
        most_recent_logs = '#{}:\n'.format(i.isoformat())
        for wlog_str in content[i]:
            hours = wlog_str.split(' ')[0]
            start_time = wlog_str.split(' ')[1]
            issue_key = wlog_str.split(' ')[2]
            description = " ".join(wlog_str.split(' ')[3:])
            time_spent_seconds = calculate_seconds(float(hours))
            account_id = os.getenv("TEMPO_ACCOUNT_ID")
            issue_id = get_issue_id(issue_key)
            if issue_id == -1:
                msg = 'Could not find issue key: {}'.format(issue_key)
                logging.log(logging.INFO, msg)
                imports_ok = False
            date_from = i.isoformat()
            most_recent_logs = most_recent_logs + '#- {} {} {} {}\n'.format(
                hours, start_time, issue_key, description)
            try:
                logged_wl = tempo.create_worklog(
                    accountId=account_id,
                    issueId=issue_id,
                    dateFrom=date_from,
                    timeSpentSeconds=time_spent_seconds,
                    description=description,
                    startTime=start_time,
                    billableSeconds=time_spent_seconds
                )
                if logged_wl['issue']['id'] not in issue_ids:
                    issue_ids[logged_wl['issue']['id']] = issue_key
                logged[logged_wl['tempoWorklogId']] = {
                    "Date": logged_wl['startDate'],
                    "Time": logged_wl['startTime'],
                    "Key": issue_ids[logged_wl['issue']['id']],
                    "Duration": calculate_hours(logged_wl['timeSpentSeconds'])
                }
                imports_ok = True
            except Exception:
                msg = 'Could not import the worklog: {}'.format(wlog_str)
                logging.log(logging.INFO, msg)
                imports_ok = False

# Kontrolle
if len(logged) > 0 and imports_ok:
    print('These Worklogs were logged:')
    for wl in logged:
        print(logged[wl])

# YML-Datei ins Archiv verschieben
if imports_ok:
    file_suffix = datetime.now().strftime('%Y%m%d%H%M%S')
    os.replace(args.worklogs, 'archive/worklog_{}.yml'.format(file_suffix))
    msg = 'Worklog file archived'
    logging.log(logging.INFO, msg)

# Neues YML-Template anlegen
if imports_ok:
    with open(args.worklogs, 'w') as file:
        file.write(most_recent_logs)

sys.exit(0)
