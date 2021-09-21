# aws-s3-athena

This DAG shows how to connect aws services to contruct workflow.

## Before triggering DAG
set `aws_demo` in Connections with your token, check [link](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/connections/aws.html) for the tutorial,
you can set from UI or using below command

```bash
docker exec -it <container_id_or_name> airflow connections add --conn-type aws --conn-login ${AWS_ACCESS_KEY_ID} --conn-password ${AWS_SECRET_ACCESS_KEY} --conn-extra '{"region_name":"us-west-2", "aws_session_token":"'"${AWS_SESSION_TOKEN}"'"}' aws_demo
```

If there's need to delete `aws_demo` connection

```bash
docker exec -it <container_id_or_name> airflow connections delete aws_demo
```

## Pipeline

* wait_S3_key: wait for key in S3 bucket. After triggering DAG, run below command and observe the status of sensor

```bash
aws s3 cp dags/aws/trigger.txt s3://mybucket/trigger.txt
```

* download_s3_file: download file and read the content using custom `S3DownloadOperator`, the result shows in xcom with `return_value` as key and file content as value
* run_athena: run athena with the sql contains content from file, and the result folder is `s3://mybucket/demo_{{ ds }}`.
Check rendered value from UI to observe the result of `{{ ds }}`
* list_s3_files: list files in `s3://mybucket/demo_{{ ds }}`, it should contains the athena result
