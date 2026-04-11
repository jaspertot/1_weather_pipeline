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
