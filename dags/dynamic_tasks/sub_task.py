import time
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago


default_args = {
    'owner': 'sh',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}

def _sleep(**kwargs):
    print(kwargs["name"], kwargs["date"], kwargs["ds_from_context"])
    time.sleep(kwargs["secs"])

with DAG(
    'dynamic_sub_task',
    default_args=default_args,
    start_date=days_ago(1),
    description='demo how to generate dynamic task from variable',
    schedule_interval=None,
    catchup=False,
    tags=["sh", "dynamic", "subtask"],
) as dag:

    # get from main dag
    name = '{{ dag_run.conf["name"] }}'
    date = '{{ dag_run.conf["date"] }}'
    ds_from_main_context = '{{ dag_run.conf["ds_from_context"] }}'

    grpStart = PythonOperator(
        task_id='subtask_start',
        python_callable=_sleep,
        op_kwargs={
            "secs":3,
            "name": name,
            "date": date,
            "ds_from_context": ds_from_main_context
        },
    )
    grpEnd = DummyOperator(
        task_id='subtask_end',
    )
    grpStart >> grpEnd
