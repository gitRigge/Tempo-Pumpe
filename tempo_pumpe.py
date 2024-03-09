import os
import logging
import yaml
import sys
import argparse
from datetime import datetime
from tempoapiclient import client_v4
from atlassian import Jira

def calculate_seconds(hours: float):
    return int(hours*60*60)

def calculate_hours(seconds: int):
    return float(seconds/60/60)

def get_issues():
    ids = {}
    with open('.issues.yml', 'r') as file:
        keys = yaml.safe_load(file)
    for i in keys:
        ids[keys[i]] = i
    return keys, ids

def set_issues(issue_key: str, issue_id: int, summary: str):
    with open('.issues.yml', 'a') as file:
        file.write('{}: {}\t#{}'.format(issue_key, issue_id, summary))

def get_issue_id(issue_key: str):
    global issue_keys
    if not issue_key in issue_keys:
        # JIRA Rest Client
        jira = Jira(
            url=os.getenv("JIRA_BASE_URL"),
            username=os.getenv("JIRA_USER"),
            password=os.getenv("JIRA_TOKEN"),
            cloud=True
        )
        # API Call
        try:
            issue = jira.issue(key=issue_key, fields='id')
            issue_id = issue['id']
            summary = issue['fields']['summary']
            set_issues(issue_key, issue_id, summary)
            return int(issue_id)
        except Exception:
            return -1
    else:
        return issue_keys[issue_key]

logging.basicConfig(
    filename=r'logs\worklog_pumpe.log',
    format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s',
    encoding='utf-8',
    level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('worklog')
args = parser.parse_args()

# Tempo REST Client
tempo = client_v4.Tempo(
    auth_token=os.getenv("TEMPO_TOKEN"),
    base_url=os.getenv("TEMPO_BASE_URL")
)

# Recent issues
issue_keys,issue_ids = get_issues()

# Worklogs
with open(args.worklog, 'r') as file:
    content = yaml.safe_load(file)

imports_ok = False

if len(content):
    logged = {}
    for i in content:
        for wlog_str in content[i]:
            hours = wlog_str.split(' ')[0]
            start_time = wlog_str.split(' ')[1]
            issue_key = wlog_str.split(' ')[2]
            description = wlog_str.split(' ')[3]
            time_spent_seconds = calculate_seconds(float(hours))
            account_id = os.getenv("TEMPO_ACCOUNT_ID")
            issue_id = get_issue_id(issue_key)
            if issue_id == -1:
                msg = 'Could not find issue key: {}'.format(issue_key)
                logging.log(logging.INFO, msg)
                imports_ok = False
            date_from = i.isoformat()
            try:
                logged_wl = tempo.create_worklog(
                    accountId=account_id,
                    issueId=issue_id,
                    dateFrom=date_from,
                    timeSpentSeconds=time_spent_seconds,
                    description=description,
                    startTime=start_time
                )
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
    os.replace(args.worklog, 'archive/worklog_{}.yml'.format(file_suffix))
    msg = 'Worklog file archived'
    logging.log(logging.INFO, msg)

sys.exit(0)