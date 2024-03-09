# Tempo-Pumpe
Tool to push worklogs to Tempo Timesheets / Atlassian JIRA


## Requirements

See 'requirements.txt'


## Configuration

'tempo_pumpe' requires some environment variables to run properly


### Required environment variables

These environment variables are required

* "TEMPO_ACCOUNT_ID" = "your_jira_account_id"
* "TEMPO_TOKEN" = "your_tempo_api_key"
* "JIRA_USER" = "your_jira_username"
* "JIRA_BASE_URL" = "your_jira_base_url"
* "JIRA_TOKEN" = "your_jira_api_token"

### Additional optional environment variables

These environment variables are optional

* "TEMPO_BASE_URL" = "tempo_api_url_of_your_region"
* "HTTP_PROXY" = "your_http_proxy_url"
* "HTTPS_PROXY" = "your_https_proxy_url"


## Sample 'worklogs.yml'

'tempo_pumpe' reads your worklogs from a YAML file like this

```
2017-02-06:
- 0.5 8:30 DUM-1 Investigating a problem with our external database system
- 3.0 9:00 DUM-2 Testing new implementation
```


## Push your worklogs to Tempo Timesheets

Run the following command

```
python3 tempo_pumpe.py worklogs.yml
```


## Questions & Answers

Here are some common questions and answers.


### What does the tool?

With the '-i' or '--import' parameter, you point to your worklog logged
in a YAML file. The tool reads and parses the YAML file. It then loops
through each parsed day. For each day, it loops through each worklog.
Then, it pushes each worklog via the REST to the Tempo Timesheet API.
Successfully created worklogs are then returned from the API. The tool
collects these returned worklogs, compares it with the parsed ones and
prints a quick summary. This is meant as confirmation for you that your
worklogs have been successfully created. Finally, the tool archives your
YAML file.


### Why 'Tempo-Pumpe'?

'Tempo-Pumpe' is German and means 'Tempo pump'. This name has two meanings.
It is a tribute to the 'Vokabelpumpe' by Christian S., a tool from my school
days that helped me learn English vocabulary. At the same time, the name is
intended to indicate that the tool can be used to quickly and conveniently
pump worklogs into tempo timesheets.