from typing import Optional, Union
from datetime import timedelta

from airflow import DAG
from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.sensors.s3_key import S3KeySensor
from airflow.providers.amazon.aws.operators.athena import AWSAthenaOperator
from airflow.providers.amazon.aws.operators.s3_list import S3ListOperator
from airflow.utils.dates import days_ago
from airflow.utils.decorators import apply_defaults

docs = """
## aws-s3-athena

This DAG shows how to connect aws services to contruct workflow.

### Before triggering DAG
set `aws_demo` in Connections with your token, check [link](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/connections/aws.html) for the tutorial,
you can set from UI or using below command

```
docker exec -it <container_id_or_name> airflow connections add --conn-type aws --conn-login ${AWS_ACCESS_KEY_ID} --conn-password ${AWS_SECRET_ACCESS_KEY} --conn-extra '{"region_name":"us-west-2", "aws_session_token":"'"${AWS_SESSION_TOKEN}"'"}' aws_demo
```

If there's need to delete `aws_demo` connection

```
docker exec -it <container_id_or_name> airflow connections delete aws_demo
```

### Pipeline

* wait_S3_key: wait for key in S3 bucket. After triggering DAG, run below command and observe the status of sensor

```
aws s3 cp dags/aws/trigger.txt s3://mybucket/trigger.txt
```

* download_s3_file: download file and read the content using custom `S3DownloadOperator`, the result shows in xcom with `return_value` as key and file content as value
* run_athena: run athena with the sql contains content from file, and the result folder is `s3://mybucket/demo_{{ ds }}`.
Check rendered value from UI to observe the result of `{{ ds }}`
* list_s3_files: list files in `s3://mybucket/demo_{{ ds }}`, it should contains the athena result

"""

class S3DownloadOperator(BaseOperator):
    # let bucket_key accept jinja template string
    template_fields = ('bucket_key',)

    @apply_defaults
    def __init__(self, bucket_key, bucket_name, aws_conn_id: str = 'aws_demo',
        verify: Optional[Union[bool, str]] = None, *args, **kwargs):
        super(S3DownloadOperator, self).__init__(*args, **kwargs)
        self.aws_conn_id = aws_conn_id
        self.bucket_key = bucket_key
        self.bucket_name = bucket_name
        self.verify = verify

    def execute(self, context):
        s3conn = S3Hook(aws_conn_id=self.aws_conn_id, verify=self.verify)
        self.log.info("Downloading source S3 file s3://%s/%s", self.bucket_name, self.bucket_key)
        if not s3conn.check_for_key(self.bucket_key, self.bucket_name):
            raise AirflowException(f"The source key s3://{self.bucket_name}/{self.bucket_key} does not exist")
        content = s3conn.select_key(key=self.bucket_key, bucket_name=self.bucket_name, expression=False)
        return content


default_args = {
    'owner': 'sh',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'aws_s3_athena',
    default_args=default_args,
    start_date=days_ago(1),
    description='demo for etl that using serveral aws services',
    schedule_interval=None,
    catchup=False,
    tags=["sh", "aws", "athena", "s3"]
) as dag:

    dag.doc_md = docs

    # task to wait for s3://mybucket/trigger.txt
    # aws s3 cp dags/aws/trigger.txt s3://mybucket/trigger.txt
    waitS3file = S3KeySensor(
        task_id="wait_S3_key",
        aws_conn_id='aws_demo',
        bucket_key="trigger.txt",
        bucket_name="mybucket",
        mode="reschedule",
        poke_interval=10, # Time in seconds that the job should wait in between each tries
        timeout=120,      # Time in seconds that task waiting for the file
    )

    # download file from S3 and xcom_push the content
    dl_s3_file = S3DownloadOperator(
        task_id="download_s3_file",
        aws_conn_id='aws_demo',
        bucket_key="trigger.txt",
        bucket_name="mybucket",
    )

    # retrieve content from `download_s3_file` and put it to SQL query
    # Note: `output_location` is templated so it accepts jinja string `{{ ds }}`
    run_athena = AWSAthenaOperator(
        task_id="run_athena",
        aws_conn_id = "aws_demo",
        query='''select * from table where dt='{{ ti.xcom_pull(key="return_value", task_ids="download_s3_file")|trim }}' limit 10''',
        database="database",
        output_location="s3://mybucket/demo_{{ ds }}",
        workgroup="workgroup",
        sleep_time=10,
        max_tries=5,
    )

    # listing files in S3 folder
    # Note: `prefix` is templated so it accepts jinja string `{{ ds }}`
    output = S3ListOperator(
        task_id='list_s3_files',
        aws_conn_id='aws_demo',
        bucket='mybucket',
        prefix="demo_{{ ds }}/",
        delimiter='/',
    )

    # define the workflow
    waitS3file >> dl_s3_file >> run_athena >> output
