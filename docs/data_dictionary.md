# Data Dictionary

This document describes all columns in the two Supabase tables used by the Weather Data Pipeline.

---

## Table: raw_weather

Stores the raw weather data exactly as received from the OpenWeatherMap API after flattening and field selection. This is the bronze layer — no transformations applied.

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `city` | VARCHAR(100) | No | City name as returned by the API | Sagada |
| `country` | VARCHAR(10) | Yes | ISO 3166-1 alpha-2 country code | PH |
| `lat` | FLOAT | Yes | Latitude coordinate of the city | 17.0847 |
| `lon` | FLOAT | Yes | Longitude coordinate of the city | 120.9014 |
| `weather_main` | VARCHAR(50) | Yes | Broad weather category | Clear |
| `weather_desc` | VARCHAR(100) | Yes | Detailed weather description | clear sky |
| `temp_kelvin` | FLOAT | Yes | Current temperature in Kelvin as returned by API | 289.14 |
| `feels_like_kelvin` | FLOAT | Yes | Perceived temperature in Kelvin | 288.96 |
| `humidity` | INT | Yes | Relative humidity as a percentage | 83 |
| `pressure` | INT | Yes | Atmospheric pressure at city level in hPa | 1014 |
| `sea_level_pressure` | INT | Yes | Atmospheric pressure at sea level in hPa | 1014 |
| `ground_level_pressure` | INT | Yes | Atmospheric pressure at ground level in hPa | 863 |
| `wind_speed` | FLOAT | Yes | Wind speed in metres per second | 1.3 |
| `wind_deg` | INT | Yes | Wind direction in meteorological degrees (0-360) | 111 |
| `wind_gust` | FLOAT | Yes | Wind gust speed in m/s — null when conditions are calm | 1.02 |
| `visibility` | INT | Yes | Horizontal visibility in metres — max value is 10000 | 10000 |
| `clouds_pct` | INT | Yes | Cloud coverage as a percentage | 14 |
| `dt` | BIGINT | No | Unix timestamp of when the weather measurement was taken | 1775389320 |
| `sunrise` | BIGINT | Yes | Unix timestamp of sunrise for that city on that day | 1775339295 |
| `sunset` | BIGINT | Yes | Unix timestamp of sunset for that city on that day | 1775383790 |
| `fetched_at` | TIMESTAMP | Yes | Datetime when the pipeline ingestion script ran | 2026-04-05 08:00:00 |

---

## Table: weather_transformed

Stores cleaned and enriched weather data. This is the silver layer — the table used by the Streamlit dashboard and all analytics queries. Contains all columns from `raw_weather` except the Kelvin temperature columns, plus additional derived columns.

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `city` | VARCHAR(100) | No | City name as returned by the API | Sagada |
| `country` | VARCHAR(10) | Yes | ISO 3166-1 alpha-2 country code | PH |
| `lat` | FLOAT | Yes | Latitude coordinate of the city | 17.0847 |
| `lon` | FLOAT | Yes | Longitude coordinate of the city | 120.9014 |
| `weather_main` | VARCHAR(50) | Yes | Broad weather category | Clear |
| `weather_desc` | VARCHAR(100) | Yes | Detailed weather description | clear sky |
| `temp_celsius` | FLOAT | Yes | Current temperature in Celsius | 16.0 |
| `feels_like_celsius` | FLOAT | Yes | Perceived temperature in Celsius | 15.8 |
| `temp_fahrenheit` | FLOAT | Yes | Current temperature in Fahrenheit | 60.8 |
| `humidity` | INT | Yes | Relative humidity as a percentage | 83 |
| `pressure` | INT | Yes | Atmospheric pressure at city level in hPa | 1014 |
| `sea_level_pressure` | INT | Yes | Atmospheric pressure at sea level in hPa | 1014 |
| `ground_level_pressure` | INT | Yes | Atmospheric pressure at ground level in hPa | 863 |
| `wind_speed` | FLOAT | Yes | Wind speed in metres per second | 1.3 |
| `wind_deg` | INT | Yes | Wind direction in meteorological degrees (0-360) | 111 |
| `wind_gust` | FLOAT | Yes | Wind gust speed in m/s — null when conditions are calm | 1.02 |
| `visibility` | INT | Yes | Horizontal visibility in metres — max value is 10000 | 10000 |
| `clouds_pct` | INT | Yes | Cloud coverage as a percentage | 14 |
| `heat_index` | FLOAT | Yes | Heat index calculated from temperature and humidity | 15.5 |
| `dt_utc` | TIMESTAMP | No | UTC timestamp of when the weather measurement was taken | 2026-04-05 08:00:00+00 |
| `date` | DATE | Yes | Date extracted from dt_utc | 2026-04-05 |
| `hour` | INT | Yes | Hour extracted from dt_utc (0-23) | 8 |
| `day_of_week` | VARCHAR(20) | Yes | Day name extracted from dt_utc | Sunday |
| `month` | INT | Yes | Month number extracted from dt_utc (1-12) | 4 |
| `sunrise` | TIMESTAMP | Yes | UTC timestamp of sunrise for that city on that day | 2026-04-05 05:48:15+00 |
| `sunset` | TIMESTAMP | Yes | UTC timestamp of sunset for that city on that day | 2026-04-05 18:09:50+00 |
| `fetched_at` | TIMESTAMP | Yes | Datetime when the pipeline ingestion script ran | 2026-04-05 08:00:00+00 |

---

## Notes

**Kelvin columns** are intentionally excluded from `weather_transformed`. The raw Kelvin values are preserved in `raw_weather` for auditability. All temperature analysis should use `temp_celsius` or `temp_fahrenheit`.

**wind_gust** is nullable in both tables. The OpenWeatherMap API omits this field when wind conditions are calm — this is expected behavior, not a data quality issue.

**dt vs fetched_at** — these are two different timestamps. `dt` is when the weather was actually measured by the weather station. `fetched_at` is when your pipeline script ran and collected the data. They will differ by a few minutes.

**heat_index** is computed using a simplified formula: `temp_celsius + (0.33 × humidity) - 4.00`. This is an approximation suitable for relative comparisons between cities rather than a precise meteorological calculation.
