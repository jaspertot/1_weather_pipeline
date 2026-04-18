# Setup Guide

This guide walks you through setting up the Weather Data Pipeline from scratch on a new machine.

---

## Prerequisites

Before starting make sure you have accounts and access to the following:

| Requirement | Where to get it | Notes |
|---|---|---|
| Python 3.11+ | python.org/downloads | Check `python --version` |
| Git | git-scm.com | Check `git --version` |
| WSL (Windows only) | Microsoft Store → Ubuntu | Required for Airflow on Windows |
| OpenWeatherMap API key | openweathermap.org | Free tier — 1M calls/month |
| AWS account | aws.amazon.com | Free tier for 12 months |
| Supabase account | supabase.com | Free tier — no credit card needed |
| GitHub account | github.com | For cloning the repository |

---  
&nbsp;
# Local Setup  
## Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/weather-pipeline.git
cd weather-pipeline
```

---

## Step 2 — Create a virtual environment

**MAC/Linux/WSL**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

If you are in windows, please utilize WSL.\
You will see `(.venv)` at the start of your terminal prompt when it is active.

---

## Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Set up credentials

Kindly create a .env file on your end.

Open `.env` and fill in all values:

```
OPENWEATHER_API_KEY=     # From openweathermap.org → API keys
AWS_ACCESS_KEY_ID=       # From AWS IAM → Users → Security credentials
AWS_SECRET_ACCESS_KEY=   # Same as above — only shown once at creation
AWS_REGION=us-east-1
S3_BUCKET_NAME=          # The exact name of your S3 bucket
SUPABASE_URL=            # From Supabase → Project Settings → API → Project URL
SUPABASE_KEY=            # From Supabase → Project Settings → API → service_role key
```

---

## Step 5 — Verify AWS setup

Make sure your S3 bucket exists with two folders:
```
your-bucket-name/
├── raw/
└── transformed/
```

---

## Step 6 — Verify Supabase setup

Make sure both tables exist in your Supabase project:
- `raw_weather`
- `weather_transformed`

If they do not exist run the SQL from [docs/data_dictionary.md](data_dictionary.md) in the Supabase SQL Editor.

---

## Step 7 — Test the pipeline manually

Run each phase in order to verify everything works:

```bash
# Phase 3 — Ingestion
python ingestion/fetch_weather.py

# Phase 5 — Transformation
python transformation/run_transformation.py

# Phase 7 — Quality checks
python quality/run_checks.py

# Phase 6 — Loading
python loading/supabase_loader.py
```

After running all four, check:
- `raw_data/` — two new CSV files should exist
- `logs/ingestion.log` — log entries should be present
- S3 bucket — new files in `raw/` and `transformed/` folders
- Supabase — new rows in both tables

---

## Step 8 — Run the dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

---

## Step 9 — Set up Airflow

Open your terminal and navigate to the project:

Run Airflow:

```bash
cd orchestration
bash start_airflow.sh
```

Access the Airflow UI at `http://{your-wsl-ip}:8080`

Get your WSL IP:
```bash
hostname -I
```

---

## Deploying to production

For deployment instructions see:
- Streamlit Cloud — deploy the dashboard publicly
- AWS EC2 — run Airflow 24/7 in the cloud

Both are covered in [docs/pipeline_phases.md](pipeline_phases.md) under Phase 10.

---

## Troubleshooting

**`ModuleNotFoundError` when running scripts**
Make sure you are running scripts from the project root directory, not from inside a subfolder:
```bash
# Correct
cd weather-pipeline
python ingestion/fetch_weather.py

# Wrong
cd ingestion
python fetch_weather.py
```

**`.env` variables not loading**
Make sure `python-dotenv` is installed and `load_dotenv()` is called at the top of your script.

**Airflow not accessible in browser**
Use your WSL IP address instead of localhost:
```bash
hostname -I  # get your WSL IP
```
Then go to `http://{wsl-ip}:8080`

**S3 upload failing**
Verify your IAM user has `AmazonS3FullAccess` policy attached and your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are correct in `.env`.

**Supabase connection failing**
Make sure you are using the `publishable` key, not the legacy `anon` key.
