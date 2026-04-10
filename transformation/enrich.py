import pandas as pd
import os
from loguru import logger

log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')

def enrich_data(dataframe):
    df = dataframe

    # Convert temp from Kelvin to Celsius
    df['temp_celsius'] = df['temp_kelvin'] - 273.15
    df['feels_like_celsius'] = df['feels_like_kelvin'] - 273.15
    df['temp_fahrenheit'] = (df['temp_celsius']*(9/5)) + 32
    logger.info('Converted temperature columns were created.')

    # Heat Index: Simplified Formula
    df['heat_index'] = df['temp_celsius'] + (0.33*df['humidity']) - 4.00
    logger.info('Heat index column was created.')

    # Parsing time stamps
    df['dt_utc'] = pd.to_datetime(df['dt'], unit='s', utc=True)
    df['date'] = df['dt_utc'].dt.date
    df['hour'] = df['dt_utc'].dt.hour
    df['day_of_week'] = df['dt_utc'].dt.day_name()
    df['month'] = df['dt_utc'].dt.month
    logger.info('Parsed timestamp columns were created.')

    # Converting timestamps to supabase compatible timestamp
    df['dt_utc'] = pd.to_datetime(df['dt'], unit='s', utc=True).dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    df['sunrise'] = pd.to_datetime(df['sunrise'], unit='s', utc=True).dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    df['sunset'] = pd.to_datetime(df['sunset'], unit='s', utc=True).dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    logger.info('Sunrise and sunset columns were converted to UTC timestamp.')

    # Drop Kelvin-related and dt columns
    drop_columns = ['temp_kelvin', 'feels_like_kelvin', 'dt']
    df = df.drop(columns=drop_columns)
    logger.info('Dropped Kelvin-related and dt columns')

    df = df.where(pd.notnull(df), other=None)
    return df