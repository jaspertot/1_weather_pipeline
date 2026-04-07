import os, glob
import pandas as pd
from loguru import logger

log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')
raw_path = output_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', '*.csv')

logger.add(log_path)
list_of_files = glob.glob(raw_path) 

latest_file_path = max(list_of_files, key=os.path.getctime)
latest_file = os.path.basename(latest_file_path)

logger.info(f"Recent CSV file is: {latest_file}")

df = pd.read_csv(latest_file_path)
row_count = len(df)

logger.info(f"Number of rows for {latest_file}: {row_count}")