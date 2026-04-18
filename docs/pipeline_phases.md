# Pipeline Phases

This document describes what each phase of the Weather Data Pipeline does, what files are involved, and what the expected output is.

---

## Phase 1 — Environment Setup

**Goal:** Set up a clean, reproducible Python development environment.

**What was done:**
- Created project folder structure with all necessary subdirectories
- Set up a Python virtual environment using `venv`
- Created `requirements.txt` with all project dependencies
- Created `.env` for credentials
- Initialized Git repository and connected to GitHub
- Added `.gitignore` to protect sensitive files

**Key files:**
```
.env
.gitignore
requirements.txt
```

---

## Phase 2 — API Setup

**Goal:** Establish access to the OpenWeatherMap API and understand the response structure.

**What was done:**
- Created a free OpenWeatherMap account
- Generated an API key
- Explored the Current Weather Data endpoint
- Selected 10 cities across Asia with varied climates
- Created `ingestion/cities.csv` with city names, latitudes, and longitudes

**Key files:**
```
ingestion/cities.csv
```

**API endpoint used:**
```
https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appId={api_key}
```

---

## Phase 3 — Ingestion Script

**Goal:** Fetch weather data for all 10 cities and save as a raw CSV file.

**What was done:**
- Written `fetch_weather.py` with the following functions:
  - `current_weather()` — calls the API for one city
  - `clean_json()` — flattens and cleans the JSON response
  - `extract_details()` — filters to 20 required fields using a mapping dictionary
  - `main()` — loops over all cities, builds results, saves to CSV
- Added `loguru` logging for all stages — INFO, SUCCESS, WARNING, ERROR, CRITICAL
- CSV is saved to `raw_data/` with a timestamp in the filename

**Key files:**
```
ingestion/fetch_weather.py
```

**Output:**
```
raw_data/raw_weather_DDMMYYY_HHMMSS.csv
logs/ingestion.log
```

**Columns saved (21 total):**
city, country, lat, lon, weather_main, weather_desc, temp_kelvin, feels_like_kelvin, humidity, pressure, sea_level_pressure, ground_level_pressure, wind_speed, wind_deg, wind_gust, visibility, clouds_pct, dt, sunrise, sunset, fetched_at

---

## Phase 4 — Cloud Setup

**Goal:** Set up all cloud infrastructure needed by the pipeline.

**AWS setup:**
- Created IAM user `weather_dev` with programmatic access
- Created IAM group `weather_pipeline` with `AmazonS3FullAccess` policy
- Created S3 bucket with two folders: `raw/` and `transformed/`

**Supabase setup:**
- Created Supabase project `Weather Data Pipeline`
- Created two tables: `raw_weather` and `weather_transformed`
- Retrieved `SUPABASE_URL` and `SUPABASE_KEY` for `.env`

**Key files:**
```
.env  ← updated with AWS and Supabase credentials
```

---

## Phase 5 — Transformation

**Goal:** Clean the raw data and derive new analytical columns.

**What was done:**

`clean.py`:
- Loads the latest raw CSV from `raw_data/`
- Handles nulls — drops rows missing critical fields, fills optional fields
- Fixes data types — ensures correct float, int, datetime types
- Deduplicates based on city + dt combination

`enrich.py`:
- Converts temperature from Kelvin to Celsius and Fahrenheit
- Computes heat index from temperature and humidity
- Parses Unix timestamp into dt_utc, date, hour, day_of_week, month columns
- Converts sunrise and sunset to readable datetimes

`run_transformation.py`:
- Calls clean then enrich in sequence
- Saves final enriched DataFrame to `raw_data/transformed_weather_timestamp.csv`

**Key files:**
```
transformation/clean.py
transformation/enrich.py
transformation/run_transformation.py
```

**Output:**
```
raw_data/transformed_weather_DDMMYYY_HHMMSS.csv
```

---

## Phase 6 — Loading to S3 and Supabase

**Goal:** Upload processed data to cloud storage and warehouse.

**What was done:**

`supabase_loader.py`:
- Finds the latest raw and transformed CSV files from `raw_data/`
- Uploads raw CSV to `s3://bucket/raw/`
- Uploads transformed CSV to `s3://bucket/transformed/`
- Inserts raw rows into Supabase `raw_weather` table
- Inserts transformed rows into Supabase `weather_transformed` table

**Key files:**
```
loading/supabase_loader.py
```

---

## Phase 7 — Data Quality Checks

**Goal:** Validate data before every load to prevent bad data reaching the warehouse.

**Checks implemented:**

 Check | Rule | Action on failure |
|---|---|---|
| Completeness | No nulls in critical columns (city, country, lat, lon, temp_celsius, humidity, dt_utc, fetched_at) | Raise ValueError, skip load |
| Temperature range | -90°C to 60°C | Raise ValueError, skip load |
| Humidity range | 0 to 100 | Raise ValueError, skip load |
| Wind speed | >= 0 | Raise ValueError, skip load |
| Freshness | dt_utc within last 2 hours | Raise ValueError, skip load |
| Row count | Matches expected city count from cities.csv | Raise ValueError, skip load |
| Uniqueness | No duplicate city + dt_utc combination | Raise ValueError, skip load |

If all checks pass the pipeline proceeds to load. If any fail the load is skipped and an error is logged.

**Key files:**
```
quality/run_checks.py
```

---

## Phase 8 — Airflow Orchestration

**Goal:** Automate the pipeline to run every hour without manual intervention.

  **What was done:**
  - Configured schedule to run every 15 minutes (`*/15 * * * *`)
  - Set retries to 3 with 5-minute delay
  - Configured email notifications on failure to `jaspercasile14@gmail.com`
  - Set `max_active_runs=1` to prevent overlapping pipeline runs
  - Created `start_airflow.sh` for local WSL startup
  - Created `start_airflow_ec2.sh` for EC2 production startup
  - Quality check task pushes status to XCom and fails explicitly if checks don't pass
  - Load task uses `trigger_rule='all_success'` to only run if quality checks pass

**Key files:**
```
orchestration/dags/weather_dag.py
orchestration/start_airflow.sh
orchestration/start_airflow_ec2.sh
```

---

## Phase 9 — Streamlit Dashboard

**Goal:** Build an interactive web dashboard to visualize the collected weather data.

**What was done:**

`queries.py`:
- `get_distinct_count()` — returns number of unique values in a specified column for a given table
- `get_latest_readings()` — retrieves latest readings ordered by `fetched_at` (descending) and `city`, with configurable limit
- `get_temperature_history()` — retrieves temperature data (city, temp_celsius, temp_fahrenheit, dt_utc, fetched_at) from the last 24 hours, optionally filtered by specific city
- `get_humidity_comparison()` — retrieves latest humidity readings (city, humidity, dt_utc, weather_main, fetched_at) ordered by `fetched_at` (descending) and `city`, with configurable limit
- `get_all_cities()` — returns sorted list of unique cities from specified table

`loading.supabase_loader.py`:
- `get_supabase_client()` — creates authenticated Supabase client using `SUPABASE_PROJECT_URL` and `SUPABASE_PUBLIC_KEY` from `.env`

`app.py`:
- Page config and header with last updated timestamp
- Sidebar with city multiselect and date range picker
- 4 metric cards — hottest, coldest, most humid, average temperature
- World map — scatter_geo with temperature color scale
- Line chart — temperature history over time
- Bar charts — humidity and heat index comparison
- Summary table — latest readings per city
- Auto-refresh toggle

**Key files:**
```
dashboard/queries.py
dashboard/app.py
```

---

## Phase 10 — Deployment

**Goal:** Make the dashboard publicly accessible and the pipeline run 24/7 without a local machine.

### Part A — Streamlit Cloud

- Pushed code to GitHub
- Created app on streamlit.io/cloud
- Added credentials as Streamlit secrets
- Dashboard accessible at public URL

### Part B — AWS EC2

- Launched `c71-flex.large` EC2 instance (free tier)
- Edit the `orchestration/in_ec2_server_setup.sh` to setup the environment in the EC2 instance with one run. This script will do the following:
  - Installed Python, Git, and project dependencies
  - Cloned repository onto EC2
  - Created `.env` with credentials
  - Configured Airflow with `AIRFLOW_HOME` pointing to `orchestration/`
  - Created `systemd` service to run Airflow as a background process
  - Pipeline now runs hourly automatically 24/7

---

## Phase 11 — Documentation

**Goal:** Document the project for other developers and portfolio purposes.

**Files created:**
```
README.md                    ← project overview and quick start
docs/architecture.md         ← system design and technology decisions
docs/data_dictionary.md      ← column definitions for all tables
docs/setup.md                ← detailed local setup instructions
docs/pipeline_phases.md      ← this file
```
