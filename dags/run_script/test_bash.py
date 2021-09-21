from datetime import timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


docs = """
## Run Script

This DAG shows how to run bash script and python script

To run bash/python script with [BashOperator](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/bash.html)

* `run_script_rendered`: Airflow try to render content in given `.sh` or `.bash` if `bash_command` is not ends with space. and file in `bash_command` is relative path from where the dag file is.

* `run_script_abspath`: If you want to run a script without rendering first, add a space at the end of `bash_command`, while also need to add `bash`
at the front to execute script without execute permission.

* `run_python_script_abspath`: add a space at the end of `bash_command`


Note:

`dags` are copied to `/opt/ariflow/dags` in this examples, while the path can be `/usr/local/airflow/dags` in other place such as [mwaa](https://aws.amazon.com/managed-workflows-for-apache-airflow/)

"""


default_args = {
    'owner': 'sh',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'test_script',
    default_args=default_args,
    start_date=days_ago(1),
    description='test script',
    schedule_interval=None,
    catchup=False,
    tags=["sh", "script"],
) as dag:

    dag.doc_md = docs

    run_templated = BashOperator(
        task_id='run_script_rendered',
        bash_command="scripts/test_rendered.sh",
    )

    run_this = BashOperator(
        task_id='run_script_abspath',
        bash_command="bash /opt/airflow/dags/run_script/scripts/test.sh wrs ",
    )

    run_this2 = BashOperator(
        task_id='run_python_script_abspath',
        bash_command="python /opt/airflow/dags/run_script/scripts/test.py ",
    )
