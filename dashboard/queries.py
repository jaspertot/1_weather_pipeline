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

def get_latest_readings(client, limit):

    try:
        response = (
            client.table('weather_transformed')
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


def get_temperature_history(client, city=None):
    day_ago = datetime.now - timedelta(hours=24)
    query = (
        client.table('weather_transformed')
        .select('temp_celsius, temp_fahrenheit')
        .gte('fetched_at', day_ago.isoformat())
        .order('fetched_at')
    )

    if city:
        query = query.eq('city', city)
    
    response = query.execute()

    return response.data
    



latest_readings= get_latest_readings(supabase_client, 10) # 10 == number of cities that we have so far in ingestion/cities.csv

for record in latest_readings:
    print(f"City: {record['city']}, Fetched at: {record['fetched_at']}")




