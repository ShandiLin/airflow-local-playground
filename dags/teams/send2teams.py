import time
from datetime import timedelta
import random

from airflow import DAG
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator
from teams.custom_ops.ms_teams_webhook_operator import MSTeamsWebhookOperator
from airflow.exceptions import AirflowFailException
from airflow.utils.dates import days_ago


docs = """
## Send message to teams channel

This DAG shows how to send message to teams channel if success in DAG and send failed message when task failed. Also it shows how to use branch operator.

Note: `ms_teams_webhook_operators` and `ms_teams_webhook_hooks` are modified from [github](https://github.com/mendhak/Airflow-MS-Teams-Operator)

### Before triggering DAG
set `msteams_webhook_url` in Connections with your webhook URL, check [Airflow-MS-Teams-Operator](https://code.mendhak.com/Airflow-MS-Teams-Operator/) for the tutorial, or set by command

```
docker exec -it <container_id_or_name> airflow connections add --conn-type http --conn-schema https --conn-host <your_webhook_url_without_https> msteams_webhook_url
```

### Pipeline

1. start
2. branching
    * lucky_you (it will always success)
    * chu_si_la (it will always failed, and send fail message to teams)
3. send_result_to_teams: if all tasks in DAG success, it will send message to teams

Notice: (2) randomly choise one branch. However, you can trigger DAG with config `{"branch": "chu_si_la"}` or `{"branch": "lucky_you"}` to force it to execute target task for testing

"""

def on_failure(context):
    dag_id = context['dag_run'].dag_id
    task_id = context['task_instance'].task_id
    logs_url = context['ti'].log_url

    teams_notification = MSTeamsWebhookOperator(
        task_id="msteams_notify_failure",
        trigger_rule="all_done",
        title=f"{dag_id} has failed on task: {task_id}",
        button_text="View log",
        button_url=logs_url,
        theme_color="FF0000",
        http_conn_id='msteams_webhook_url')
    teams_notification.execute(context)

def return_branch(**kwargs):
    branches = ['lucky_you','chu_si_la']
    if kwargs.get("branch") in branches:
        task_id = kwargs.get("branch")
        return task_id
    random.seed(time.time())
    return random.choice(branches)

def raiseException():
    raise AirflowFailException("boom!!!")


default_args = {
    'owner': 'sh',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'send_teams',
    default_args=default_args,
    start_date=days_ago(1),
    description='send message to teams',
    schedule_interval=None,
    catchup=False,
    tags=["sh", "teams"]
) as dag:

    dag.doc_md = docs

    start = DummyOperator(task_id='start')

    oneSuccess = DummyOperator(task_id='lucky_you')
    oneFailed = PythonOperator(
        task_id='chu_si_la',
        python_callable=raiseException,
        on_failure_callback=on_failure,
    )
    branching = BranchPythonOperator(
        task_id='branching',
        python_callable=return_branch,
        op_kwargs={"branch": '{{ dag_run.conf.get("branch") }}'}
    )

    # Only send message when all the tasks success
    send_success_result = MSTeamsWebhookOperator(
        task_id='send_result_to_teams',
        http_conn_id='msteams_webhook_url',
        title = "DAG: {{ dag_run.dag_id }}",
        subtitle = "date: {{ ds }}",
        text = "I'm doing good",
        theme_color = "00FF00",
        trigger_rule=TriggerRule.NONE_FAILED,
    )

    start >> branching >> [oneSuccess, oneFailed] >> send_success_result
