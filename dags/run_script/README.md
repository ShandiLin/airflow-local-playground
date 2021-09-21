# Run Script

This DAG shows how to run bash script and python script

To run bash/python script with [BashOperator](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/bash.html)

* `run_script_rendered`: Airflow try to render content in given `.sh` or `.bash` if `bash_command` is not ends with space. and file in `bash_command` is relative path from where the dag file is.

* `run_script_abspath`: If you want to run a script without rendering first, add a space at the end of `bash_command`, while also need to add `bash`
at the front to execute script without execute permission.

* `run_python_script_abspath`: add a space at the end of `bash_command`


Note:

`dags` are copied to `/opt/ariflow/dags` in this examples, while the path can be `/usr/local/airflow/dags` in other place such as [mwaa](https://aws.amazon.com/managed-workflows-for-apache-airflow/)
