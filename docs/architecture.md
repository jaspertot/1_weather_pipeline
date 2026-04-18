# Architecture

This document describes the system design, data flow, and technology decisions behind the Weather Data Pipeline.

---

## System Overview

This Weather Data Pipeline is a batch data engineering system that runs every 15 minutes. It collects real-time weather data from cities (defined in `ingestion/cities.csv`) via the OpenWeatherMap API, processes and enriches it, validates it through quality checks, stores it in Supabase (PostgreSQL cloud database), and makes it available for visualization through an interactive dashboard built with Streamlit.

---

## Data Flow

```
┌─────────────────────────────┐
│     OpenWeatherMap API      │
│  Current Weather Endpoint   │
└────────────┬────────────────┘
             │ JSON response (per city)
             ▼
┌─────────────────────────────┐
│     fetch_weather.py        │
│  • Calls API for 10 cities  │
│  • Flattens JSON response   │
│  • Extracts 20 fields       │
│  • Adds fetched_at column   │
└────────────┬────────────────┘
             │ raw CSV (10 rows × 21 columns)
             ▼
┌─────────────────────────────┐
│        raw_data/            │  ← Bronze layer (local)
│  raw_weather_timestamp.csv  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   run_transformation.py     │
│  • clean.py — nulls, types  │
│  • enrich.py — conversions  │
└────────────┬────────────────┘
             │ transformed CSV (10 rows × 27 columns)
             ▼
┌─────────────────────────────┐
│        raw_data/            │  ← Silver layer (local)
│  transformed_weather_ts.csv │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│       run_checks.py         │
│  • Validation checks        │
│  • Blocks load if any fail  │
└────────────┬────────────────┘
             │ passes all checks
             ▼
┌────────────────────────────────────────────────┐
│              supabase_loader.py                │
└───────────────┬────────────────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────────────┐
│   AWS S3     │  │      Supabase        │
│  raw/        │  │  raw_weather table   │
│  transformed/│  │  weather_transformed │
└──────────────┘  └──────────┬───────────┘
  (archive)                  │
                             ▼
                  ┌──────────────────────┐
                  │  Streamlit Dashboard │
                  │  • World map         │
                  │  • Line chart        │
                  │  • Bar charts        │
                  │  • Summary table     │
                  └──────────────────────┘
```

---

## Orchestration

All pipeline stages are coordinated by Apache Airflow running on AWS EC2:

```
ingest_task
    ↓
transform_task
    ↓
quality_task ── FAIL ──→ pipeline stops, load skipped
    ↓ PASS
load_task
```

`Note:` Please modify the email notification that is currently setup. Provide your own email.

**Schedule:** `*/15 * * * *` — runs every 15 minutes automatically
**Retries:** 3 attempts with 5-minute delay between each
**Email notifications:** Sent to `youremail.com` on task failure
**Monitoring:** Airflow UI accessible on EC2 public IP
**Concurrency:** `max_active_runs=1` prevents overlapping pipeline runs

---

## Deployment Architecture

```
┌─────────────────┐     push code      ┌─────────────────┐
│   Local machine │ ─────────────────→ │     GitHub      │
│  (development)  │                    │ (source control)│
└─────────────────┘                    └────────┬────────┘
                                                │
                                    ┌───────────┴──────────┐
                                    │                      │
                                    ▼                      ▼
                           ┌───────────────┐    ┌──────────────────┐
                           │   AWS EC2     │    │ Streamlit Cloud  │
                           │c7i-flex.large |    │   (dashboard)    │
                           │  Airflow 24/7 │    │    Public URL    │
                           └───────┬───────┘    └────────┬─────────┘
                                   │                     │
                                   ▼                     │
                           ┌───────────────┐             │
                           │    AWS S3     │             │
                           │  Raw archive  │             │
                           └───────────────┘             │
                                   |                     |
                                   |                     |
                                   ▼                     │ 
                           ┌───────────────┐             │
                           │   Supabase    │ ←───────────┘
                           │  PostgreSQL   │   (queries data)
                           └───────────────┘
```

---
