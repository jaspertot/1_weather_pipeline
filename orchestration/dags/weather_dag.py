from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, os

project_dir = os.path.join(os.path.dirname(__file__), '..', '..')
clean_path  = os.path.abspath(project_dir)

sys.path.insert(0, clean_path)

from ingestion.fetch_weather import main as ingest
from transformation.run_transformation import main as transform
from quality.run_checks import main as qc
from loading.supabase_loader import main as load

def run_quality_checks(**context):
    task_instance = context.get('task_instance')

    print("Starting quality checks...")

    quality_passed = qc()

    if quality_passed:
        task_instance.xcom_push(key='quality_status', value='passed')
        return True
    
    else: 
        task_instance.xcom_push(key='quality_status', value='failed')
        raise Exception("Quality checks failed! Downstream tasks will be skipped.")
    
default_args = {
'owner': 'jasper',  # Replace with your name or team name
'depends_on_past': False,  # Tasks don't depend on previous runs
'retries': 3,  # Number of retry attempts if a task fails
'retry_delay': timedelta(minutes=5),  # Wait 5 minutes between retries
'start_date': datetime(2026, 4, 11),  # When the DAG should start
'email_on_failure': True,  # Send email on task failure
'email_on_retry': False,  # Don't send email on retry
'email': ['jaspercasile14@gmail.com'],  # Where to send notifications
'catchup': False,  # Don't backfill past runs
}

# DAG definition
dag = DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    description='ETL Pipeline from OpenWeather API.',
    schedule='*/2 * * * *', 
    catchup=False,  # Don't run for past dates when DAG is unpaused
    max_active_runs=1,  # Only run one instance at a time (prevents overlaps)
    tags=['weather', 'pipeline', 'etl'], 
    doc_md=__doc__, # Use the module docstring as DAG documentation
)

# Task Definitions

# Ingestion --> OpenWeather API data to a raw CSV file
ingest_task = PythonOperator(
    task_id='ingest_weather_data',
    python_callable=ingest,
    dag=dag, # Associate this task with the created DAG above
)

transform_task = PythonOperator(
    task_id='transform_weather_data',
    python_callable=transform,
    dag=dag
)

quality_task = PythonOperator(
    task_id='quality_check_data',
    python_callable=qc,
    dag=dag,
    # provide_context=True # Check the run_quality_checks function above. To be used in the parameter
)

load_task = PythonOperator(
    task_id='load_to_supabase',
    python_callable=load,
    dag=dag,
    trigger_rule='all_success'
)

# Task Dependency Definition

ingest_task >> transform_task >> quality_task >> load_task