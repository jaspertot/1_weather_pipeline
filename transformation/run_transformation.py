import os
from transformation.clean import clean_data
from datetime import datetime
from transformation.enrich import enrich_data
from loguru import logger

current_datetime = timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
output_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', f'transformed_weather_{current_datetime}.csv')

def main():
    df = clean_data()
    df = enrich_data(df)

    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.success(f'transformed_weather_{current_datetime}.csv successfully saved!')

if __name__ == "__main__":
    main()