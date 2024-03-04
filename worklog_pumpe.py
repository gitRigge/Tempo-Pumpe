import os
import logging
import yaml
from tempoapiclient import client_v4

logging.basicConfig(filename='worklog_pumpe.log', encoding='utf-8', level=logging.INFO)

def calculate_seconds(hours: float):
    return int(hours*60*60)

def calculate_hours(seconds: int):
    return float(seconds/60/60)

def get_key_by_val(value: int):
    keys = list(issue_keys.keys())
    values = list(issue_keys.values())
    if value in values:
        i = 0
        while i < len(values):
            if value == values[i]:
                break
            i += 1
        return keys[i]
    return None


with open('my_worklog.yaml', 'r') as file:
    content = yaml.safe_load(file)

if len(content):

    logged = {}

    tempo = client_v4.Tempo(
        auth_token=os.getenv("TEMPO_TOKEN"),
        base_url=os.getenv("TEMPO_BASE_URL"),
        #proxies=proxies  # Not yet implemented in module
    )

    tempo.search_worklogs()

    for i in content:
        for wlog_str in content[i]:
            hours = wlog_str.split(' ')[0]
            start_time = wlog_str.split(' ')[1]
            issue_key = wlog_str.split(' ')[2]
            description = wlog_str.split(' ')[3]
            time_spent_seconds = calculate_seconds(float(hours))
            account_id = os.getenv("TEMPO_ACCOUNT_ID")
            issue_id = issue_keys[issue_key]
            date_from = i.isoformat()
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
                "Key": get_key_by_val(logged_wl['issue']['id']),
                "Duration": calculate_hours(logged_wl['timeSpentSeconds'])
            }

# Kontrolle
print(logged)

# YML-Datei ins Archiv verschieben
