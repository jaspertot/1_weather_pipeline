import os, sys
import pandas as pd
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta, timezone

# Adding the 1_weather_pipeline to Python path, to utilize function from other code.
sys.path.insert(0, str(Path(__file__).parent.parent)) 
from loading.supabase_loader import latest_file

log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')

# logger.add(log_path)
if not logger._core.handlers:
    logger.add(log_path)

def load_transformed_csv():
    transformed_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', 'transformed_weather_*.csv')

    lf_path, l_file = latest_file(transformed_path)
    logger.info(f'Latest transformed file is: {l_file}')
    
    df = pd.read_csv(lf_path)

    return df

def get_count_cities():
    cities_path = os.path.join(os.path.dirname(__file__), '..', 'ingestion', 'cities.csv')
    
    df = pd.read_csv(cities_path)
    num_rows = len(df)

    logger.info(f'Expected number of cities are: {num_rows}')
    return num_rows

def check_null(df):
    required_columns = ['city', 'country', 'lat', 'lon', 'temp_celsius', 'humidity', 'dt_utc', 'fetched_at']
    
    for col in required_columns:
        if df[col].isnull().any():
            logger.error(f'Null values found in column: {col}')
            raise ValueError(f'Null values found in column: {col}')
    
    logger.info('No null values found on critical columns.')
    
def check_temp_humidity(df, temp_column, humidity):
    temp = df[temp_column]
    humidity = df[humidity]

    if (temp < -90).any() or (temp > 60).any():
        logger.error('Temp value out of bounds.')
        raise ValueError('Temp value out of bounds.')
    
    logger.info('Temp value within bounds.')

    if (humidity < 0).any() or (humidity > 100).any():
        logger.error('Humidity value out of bounds.')
        raise ValueError('Humidity value out of bounds.')
    
    logger.info('Humidity value within bounds.')

def check_wind_speed(df, wind_speed):
    w_speed = df[wind_speed]

    if (w_speed < 0).any():
        logger.error('Min. wind speed value not reached.')
        raise ValueError('Min. wind speed value not reached.')
    
    logger.info('Min. wind speed value reached.')

def check_freshness(df, dt_utc, threshold):
    df[dt_utc] = pd.to_datetime(df[dt_utc])

    now = datetime.now(timezone.utc) 
    diff = now - timedelta(hours=threshold)

    if(df[dt_utc] < diff).any():
        old_timestamps = df[df[dt_utc] < diff]
        logger.error(f'Found {len(old_timestamps)} timestamp(s) older than {threshold} hours')
        raise ValueError(f'Timestamps exceed {threshold} hours old')
    
    logger.info(f'All timestamps within last {threshold} hours')

def check_row_count(df, csv_row_count):
    if len(df) != csv_row_count:
        logger.error('The length of the dataframe does not match the origin.')
        raise ValueError('The length of the dataframe does not match the origin.')
    
    logger.info('Number of rows in the dataframe matched the origin.')

def check_duplicates(df, city, dt_utc):
    duplicates = df.duplicated(subset=[city, dt_utc])

    if duplicates.any():
        duplicate_count = duplicates.sum()
        logger.error(f'Found {duplicate_count} duplicate row(s) based on {city} and {dt_utc}')
        raise ValueError(f'Duplicates found in {city} + {dt_utc} combination')
    
    logger.info(f'No duplicates found in {city} + {dt_utc} combination')

def run_all_checks(df, expected_rows):
    try:
        # Quality Checks
        check_null(df)
        check_temp_humidity(df, 'temp_celsius', 'humidity')
        check_wind_speed(df, 'wind_speed')
        check_freshness(df, 'dt_utc', 2)
        check_row_count(df, expected_rows)
        check_duplicates(df, 'city', 'dt_utc')

        return True
    
    except Exception as e:
        logger.error(f"Check failed: {e}")
        return False 

def main():
    df = load_transformed_csv()
    expected_rows = get_count_cities()

    if run_all_checks(df, expected_rows):
        logger.success('Quality check successful!')
        return True
    
    else:
        logger.error('Error encountered during quality check.')
        return False


if __name__ == "__main__":
    main()
