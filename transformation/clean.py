import os, glob
import pandas as pd
from loguru import logger
from datetime import datetime

# Path definition
log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')
raw_path = output_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', '*.csv')

duplicates = 0
# Points to log file
logger.add(log_path)

def clean_data():
    list_of_files = glob.glob(raw_path) 
    latest_file_path = max(list_of_files, key=os.path.getctime)
    latest_file = os.path.basename(latest_file_path)
    logger.info(f"Recent CSV file is: {latest_file}")

    df = pd.read_csv(latest_file_path)
    row_count = len(df)

    logger.info(f"Number of rows for {latest_file}: {row_count}")

    # Cleaning Null Values
    nn_columns = [
        'city', 
        'country', 
        'lat', 
        'lon', 
        'temp_kelvin', 
        'humidity', 
        'dt'
    ]

    df = df.dropna(subset=nn_columns)

    # Handling ground_level and sea_level pressure
    df = df.fillna({
        'ground_level_pressure': df['pressure'],
        'sea_level_pressure': df['pressure']
    })

    # Filling visibility, if NULL with 0
    df['visibility'] = df['visibility'].fillna(0)
    logger.info("Null values were handled.")

    # Adding fetched_at column
    df['fetched_at'] = datetime.now()
    logger.info("'fetched_at' column is created.")

    # Convert some columns to their respective dtypes
    df = df.astype({
        'city': 'string',
        'country': 'string',
        'wind_gust': 'float64'
    })
    logger.info(f'Converted rows to their respective data types.')

    # Removing duplicates
    logger.info(f'Cleaned {df.duplicated(subset=['city', 'dt']).sum()} duplicates.')
    df = df.drop_duplicates(subset=['city', 'dt'], keep='first')
    logger.info(f'After dropping duplicates, the dataframe has {len(df)} rows')
    
    return df

