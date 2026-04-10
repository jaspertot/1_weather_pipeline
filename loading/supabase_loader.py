import os, glob, boto3, math
import pandas as pd

from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from supabase import create_client, Client

load_dotenv(override=True)
log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')
logger.add(log_path)

raw_path  = os.path.join(os.path.dirname(__file__), '..', 'raw_data', 'raw_weather_*.csv')
transformed_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', 'transformed_weather_*.csv')

current_datetime = timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')

def validate_aws_credentials():
    
    """Validate that AWS credentials are properly configured"""
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing AWS credentials: {', '.join(missing_vars)}")

    else:
        logger.info(f"Crendentials found.")
    
    try:
        # Test the credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"Authenticated as: {identity['Arn']}")
        return True
    except ClientError as e:
        logger.error(f"Invalid credentials: {e}")
        return False

def get_s3_client():
    if validate_aws_credentials():
        s3 = boto3.client('s3')
    return s3

def latest_file(filepath):
    list_of_files = glob.glob(filepath) 
    latest_file_path = max(list_of_files, key=os.path.getctime)
    latest_file = os.path.basename(latest_file_path)

    return latest_file_path, latest_file

def get_supabase_client(url, key) -> Client:
    
    supabase = create_client(url, key)

    try:
        supabase.auth.get_session()
        logger.success('Supabase API is reachable and Key is valid.')
        return supabase
    except Exception as e:
        logger.error(f'Connection failed: {e}')
  
def upload_to_s3(client, fromPath, bucket, toPath):
    # Upload files
    client.upload_file(fromPath, bucket, toPath) # Upload raw file
    logger.success(f'File successfull uploaded to {toPath}.')

def insert_into_supabase(client, filepath, table_name):
    df = pd.read_csv(filepath)
    data = df.to_dict(orient='records')
    clean_data = [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
        for row in data
    ]

    client.table(table_name).insert(clean_data).execute()


def main():
    url = os.getenv('SUPABASE_PROJECT_URL')
    key = os.getenv('SUPABASE_PUBLIC_KEY')
    bucket   = os.getenv('S3_BUCKET_NAME')

    # Retrieve latest file path
    latest_raw_fp, latest_raw_file = latest_file(raw_path)
    latest_trns_fp, latest_trns_file = latest_file(transformed_path)

    # Define S3 object
    raw_obj  = f'raw/{latest_raw_file}'
    trns_obj = f'transformed/{latest_trns_file}'

    # Initialize client
    s3_client       = get_s3_client() # Initialize S3 client
    supabase_client = get_supabase_client(url, key) # Initialize Supabase client

    # Upload to S3
    upload_to_s3(s3_client, latest_raw_fp, bucket, raw_obj)     # Upload raw file
    upload_to_s3(s3_client, latest_trns_fp, bucket, trns_obj)   # Upload transformed file

    # INSERT INTO Supabase
    insert_into_supabase(supabase_client, latest_trns_fp, 'weather_transformed')
    logger.success('Records successfully inserted to weather_transformed table.')
    insert_into_supabase(supabase_client, latest_raw_fp, 'raw_weather')
    logger.success('Records successfully inserted to raw_weather table.')

    
if __name__ == "__main__":
    main()