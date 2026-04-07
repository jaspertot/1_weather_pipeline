import requests, os, csv, re, sys

from dotenv import load_dotenv
from json_flatten import flatten
from datetime import datetime
from loguru import logger

load_dotenv()

api_key = os.getenv('OPEN_WEATHER_MAP_API_KEY')
current_datetime = timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')

city_data = {} # Dictionary populated from cities.csv
final_data = []

log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')
csv_path = os.path.join(os.path.dirname(__file__), 'cities.csv')
output_path = os.path.join(os.path.dirname(__file__), '..', 'raw_data', f'raw_weather_{current_datetime}.csv')

logger.add(log_path)

def current_weather(lat, lon):
    r=requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appId={api_key}')
    flattened_json = flatten(r.json())

    return flattened_json

def clean_json(flat_weather):
    cleaned = {}

    for key, value in flat_weather.items(): 
        clean_key = key.split('$')[0]
        clean_key = re.sub(r'\.\[\d+\]', '', clean_key) # Regex that removes the array notation
        clean_key = clean_key.replace('.', '_')

        if '$float' in key:
            cleaned[clean_key] = float(value)
        elif '$int' in key:
            cleaned[clean_key] = int(value)
        else:
            cleaned[clean_key] = value
    
    return cleaned

def extract_details(clean_json):
    final = {}
    column_mapping = {
        'coord_lat':      'lat',
        'coord_lon':      'lon',
        'weather_main':   'weather_main',
        'weather_description': 'weather_desc',
        'main_temp':      'temp_kelvin',
        'main_feels_like':'feels_like_kelvin',
        'main_humidity':  'humidity',
        'main_pressure':  'pressure',
        'main_sea_level': 'sea_level_pressure',
        'main_grnd_level':'ground_level_pressure',
        'wind_speed':     'wind_speed',
        'wind_deg':       'wind_deg',
        'wind_gust':      'wind_gust',
        'visibility':     'visibility',
        'clouds_all':     'clouds_pct',
        'dt':             'dt',
        'sys_country':    'country',
        'sys_sunrise':    'sunrise',
        'sys_sunset':     'sunset',
        'name':           'city'
    }

    for orig_key, final_key in column_mapping.items():
        final[final_key] = clean_json.get(orig_key, None)

    return final

logger.info('Data Ingestion Started.')

# Context Manager to retrieve cities, lat, and lon in the cities.csv file

try:
    with open(csv_path, 'r', encoding='utf-8') as c_file: # c_file -> cities file
        reader = csv.DictReader(c_file)  # Reads first row as headers
        for row in reader:
            city = row['City']
            city_data[city] = {
                'lat': float(row['Lat']),
                'lon': float(row['Lon'])
            }
except Exception:
    logger.critical("cities.csv not found — cannot proceed")
    sys.exit()       

if not api_key:
    logger.critical("API key missing from .env — cannot proceed")
    sys.exit()

for city in city_data.keys():
    flattened_json = current_weather(city_data[city]['lat'], city_data[city]['lon'])
    logger.info(f'Retrieved weather data from the API for {city}.')

    cleaned_flat = clean_json(flattened_json)
    logger.info("Flattened JSON cleaned.")

    final = extract_details(cleaned_flat)
    final_data.append(final)
    
    if final.get("wind_gust") is None:
        logger.warning(f"wind_gust missing for {city} — defaulting to None")
    logger.success(f'Required columns successfully extracted for {city}.')
    
logger.success('Final list prepared. Ready for saving.')

# Open context manager to write
with open(output_path, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=final_data[0].keys())
    writer.writeheader()  # Write column names
    writer.writerows(final_data)
    logger.success(f'raw_weather_{current_datetime} successfully saved!')

logger.info('Data Ingestion Completed.')