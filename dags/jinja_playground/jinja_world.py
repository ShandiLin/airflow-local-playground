from datetime import timedelta
from pprint import pprint

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


docs = """
## Jinja playground

This DAG shows all rendered values within task's context

[airflow macros](https://airflow.apache.org/docs/apache-airflow/stable/macros-ref.html)

"""

default_args = {
    'owner': 'sh',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}

def _print_conf(**kwargs):
    print("=====  my value =====")
    print("dagrun trigger type:", eval(kwargs['dagrun_trigger_type']))
    print("execution_date - 28 days:", kwargs['ds_minus28'])

    print("=====  all rendered value =====")
    pprint(kwargs)
    kwargs["ti"].xcom_push(key="gift", value="hello")


with DAG(
    'jinja_playground',
    default_args=default_args,
    start_date=days_ago(1),
    description='demo some jinja use case',
    schedule_interval=None, # change it and observe the output of rendered template
    catchup=False,
    tags=["sh", "jinja"],
) as dag:

    dag.doc_md = docs

    # The execution date as YYYY-MM-DD, and is the day before $TODAY
    # ref. https://airflow.apache.org/docs/apache-airflow/stable/macros-ref.html
    # E.g., start time: 2021/08/05 00:00 UTC, ds: 2021-08-04, tomorrow_ds: 2021-08-05
    ext_date = '{{ dag_run.conf["date"] if dag_run.conf.get("date") else ds }}'

    print_conf = PythonOperator(
        task_id="check_conf",
        python_callable=_print_conf,
        op_kwargs={
            "dagrun_trigger_type": '"manual" if {{ dag_run.external_trigger }} else "scheduled"',
            "ds_minus28": "{{ macros.ds_add(ds, -28) }}",
        }
    )

    receiver = BashOperator(
        task_id="receiver",
        bash_command='echo {{ ti.xcom_pull(task_ids="check_conf", key="gift") }}',
    )

    # DAG level dependencies
    print_conf >> receiver
