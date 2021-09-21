# Airflow Examples

> apache/airflow version: `2.1.3`
>> other 2.X versions might also work, just hasn't tested

[Offical Doc: Run Airflow in Docker](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html)

There are 3 kinds of [executors](https://airflow.apache.org/docs/apache-airflow/stable/executor/index.html#executor-types) provided for local testing. Aims to quickly test DAGs for the parsing error.

* [`SequentialExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/executor/sequential.html): scheduler can only run tasks one by one, since `sqlite` can not accept multiple connections. All the airflow components are in one container.
    * data in `sqlite` is not preserved, shutdown airflow cleans all the data.
        * create empty `./airflow.db` for the first time and use volume to preserve data if needed.
* [`LocalExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/executor/local.html): workers executes tasks concurrently. Scheduler and workers are in same container.
    * data in `posgresql` is preserved with volume
* [`CeleryExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html): scheduler sends task to redis queue, celery workers pull tasks from queue and execute, which is same as offcial [docker-compose](https://airflow.apache.org/docs/apache-airflow/2.1.3/docker-compose.yaml) file
    * data in `posgresql` is preserved with volume

## Start Airflow

### [All] Set UID and GID to `.env`

On Linux, the mounted volumes in container use the native Linux filesystem user/group permissions, so make sure the container and host computer have matching file permissions.

```bash
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env
```

### [LocalExecutor/CeleryExecutor] Init Airflow

Run for the first time, which helps to
* Check resources and print airflow version
* Create `logs` and `plugins` folders
* Run database migrations and create the first user account
    * Since table schema has been evolved, scheduler can not run successfully without migrations first

End log message as below
```bash
airflow-init_1       | Upgrades done
airflow-init_1       | [2021-09-06 02:35:47,963] {manager.py:788} WARNING - No user yet created, use flask fab command to do it.
airflow-init_1       | Admin user airflow created
airflow-init_1       | 2.1.3
airflow-examples_airflow-init_1 exited with code 0
```

`SequentialExecutor` does not need this step, since the commands (without checking resources and airflow version) in `airflow-init` is merged to one container which runs when `up`.

* `LocalExecutor`

```bash
docker-compose -f docker-compose-local.yaml up airflow-init
```

* `CeleryExecutor`

```bash
docker-compose -f docker-compose-celery.yaml up airflow-init
```

### [All] Up and Down

It takes some time for airflow to start, wait patiently for UI in `localhost:8080`

* `SequentialExecutor`
```bash
docker-compose -f docker-compose-sequentail.yaml up -d
docker-compose -f docker-compose-sequentail.yaml down
```

* `LocalExecutor`

```bash
docker-compose -f docker-compose-local.yaml up -d
docker-compose -f docker-compose-local.yaml down
```

* `CeleryExecutor`

```bash
docker-compose -f docker-compose-celery.yaml up -d
docker-compose -f docker-compose-celery.yaml down
```

## Login

default user and pwd are both `airflow`, which can be set by `_AIRFLOW_WWW_USER_USERNAME` and `_AIRFLOW_WWW_USER_PASSWORD`

## Check DAG examples

All the dags in `dags` folder contains `sh` label which can be used to filter DAGs with UI. Check `README.md` or markdown in DAG for how to trigger and observe the result.

### Examples given by airflow

Since `AIRFLOW__CORE__LOAD_EXAMPLES` is `true` in `docker-compose-*.yaml`, airflow example dags will also show in UI which is useful for learning how to contruct DAGs.

## Debug DAGs on the fly

dag folder path in container is `/opt/airflow/dags`, use `docker cp` command to copy dag files in local to the path in `scheduler` container after `docker-compose up`. Click refresh DAG button from UI and it is expected to change DAG without restarting all docker containers

Where is scheduler?
* `docker-compose-sequential.yaml`: `airflow-service`
    * container name: `airflow-examples_airflow-service_1`
* `docker-compose-local.yaml`: `airflow-scheduler`
    * container name: `airflow-examples_airflow-scheduler_1`
* `docker-compose-celery.yaml`: `airflow-scheduler`
    * container name: `airflow-examples_airflow-scheduler_1`

Note: If using `airflow < 1.10.7` without dag serialization, dag files should be copied to both webserver and scheduler. Check [dag-serialization](https://airflow.apache.org/docs/apache-airflow/stable/dag-serialization.html) for more details.
