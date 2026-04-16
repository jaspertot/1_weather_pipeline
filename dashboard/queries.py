import os, sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

project_dir = os.path.join(os.path.dirname(__file__), '..')
clean_path  = os.path.abspath(project_dir)

sys.path.insert(0, clean_path)
from loading.supabase_loader import get_supabase_client

load_dotenv(override=True)

url = os.getenv('SUPABASE_PROJECT_URL')
key = os.getenv('SUPABASE_PUBLIC_KEY')

supabase_client = get_supabase_client(url, key)

def get_distinct_count(client, table, column):
    response = (
        client.table(table)
        .select(column)
        .execute()
    )

    unique_values = set([row[column] for row in response.data])
    return len(unique_values)

def get_latest_readings(client, table, limit):
    try:
        response = (
            client.table(table)
            .select('*')
            .order('fetched_at', desc=True)
            .order('city')
            .limit(limit) #Adjust accordingly if cities were to be added in ingestion/cities.csv
            .execute()
        )

        logger.info('Successfully retrieved the latest readings.')
        return response.data
    
    except Exception as e:
        logger.error(f'Error retrieving latest readings. Error: {e}')
        return []


def get_temperature_history(client, table, city=None):
    day_ago = datetime.now() - timedelta(hours=24)
    query = (
        client.table(table)
        .select('city, temp_celsius, temp_fahrenheit, dt_utc, fetched_at')
        .gte('fetched_at', day_ago.isoformat())
        .order('fetched_at')
    )

    if city:
        query = query.eq('city', city)
    
    response = query.execute()

    return response.data

def get_humidity_comparison(client, table, limit):
    try:
        response = (
            client.table(table)
            .select('city, humidity, dt_utc, fetched_at')
            .order('fetched_at', desc=True)
            .order('city')
            .limit(limit) #Adjust accordingly if cities were to be added in ingestion/cities.csv
            .execute()
        )

        logger.info('Successfully retrieved the latest humidity readings.')
        return response.data
    
    except Exception as e:
        logger.error(f'Error retrieving latest humidity readings. Error: {e}')
        return []
    
def get_all_cities(client, table):
    try:
        # Query all city values
        response = (
            client.table(table)
            .select('city')
            .execute()
        )

        unique_cities = list(set([row['city'] for row in response.data]))
        unique_cities.sort()

        return unique_cities
    
    except Exception as e:
        print(f"Error fetching cities: {e}")
        return []
