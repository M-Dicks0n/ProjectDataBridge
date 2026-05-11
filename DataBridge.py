import requests
import json
import sqlite3
import os
from datetime import datetime


def load_config(config="config.json"):
    """Load location and unit settings from config.json"""
    with open(config, "r") as f:
        return json.load(f)


def fetch_weather_data(latitude, longitude, units):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current_weather=true"
        f"&temperature_unit={units['temperature']}"
        f"&wind_speed_unit={units['wind_speed']}"
        f"&hourly=apparent_temperature,precipitation_probability,relativehumidity_2m,windspeed_10m"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Status: 200 OK - Connection Successful!\n")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with Connection: {e}")
        return None


def transform_data(raw_json, location_name):
    """Extract all 24 hourly forecast rows for tomorrow (indices 24-47)."""
    print(f"  Processing forecast for {location_name}...")

    hourly = raw_json.get("hourly", {})
    times = hourly.get("time", [])
    apparent_temps = hourly.get("apparent_temperature", [])
    precip_probs = hourly.get("precipitation_probability", [])
    humidities = hourly.get("relativehumidity_2m", [])
    wind_speeds = hourly.get("windspeed_10m", [])

    records = []
    max_index = min(48, len(times))
    for i in range(24, max_index):
        records.append({
            "Location": location_name,
            "Forecast_datetime": times[i].replace("T", " "),
            "Apparent_temperature": float(apparent_temps[i]),
            "Precipitation_probability": int(precip_probs[i]),
            "Humidity": int(humidities[i]),
            "Wind_speed": float(wind_speeds[i]),
        })

    return records


def load_data(transformed_data):
    """Insert a single weather record into the SQLite database. Real feel= apparent_temperature """
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/weather_data.db")
    cursor = conn.cursor()

    create_table = """
                   CREATE TABLE IF NOT EXISTS weather_log
                   (
                       id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       location                  TEXT NOT NULL,
                       timestamp                 TEXT NOT NULL,
                       wind_speed                REAL,
                       apparent_temperature      REAL,
                       precipitation_probability INTEGER,
                       humidity                  INTEGER
                   );
                   """
    cursor.execute(create_table)

    insert_sql = """
                 INSERT INTO weather_log (location, timestamp, wind_speed, apparent_temperature, \
                                          precipitation_probability, humidity)
                 VALUES (?, ?, ?, ?, ?, ?);
                 """


    data_tuple = (
        transformed_data.get("Location"),
        transformed_data.get("Forecast_datetime"),
        transformed_data.get("Wind_speed"),
        transformed_data.get("Apparent_temperature"),
        transformed_data.get("Precipitation_probability"),
        transformed_data.get("Humidity"),
    )

    cursor.execute(insert_sql, data_tuple)
    conn.commit()
    conn.close()


def export_to_csv(all_records, csv_path='data/ensemble_input.csv'):
    """Write one row per forecast hour per location."""
    os.makedirs('data', exist_ok=True)
    with open(csv_path, 'w', newline='') as f:
        f.write("location,forecast_datetime,apparent_temperature,precipitation_probability,humidity,wind_speed\n")
        for record in all_records:
            f.write(
                f"{record['Location']},"
                f"{record['Forecast_datetime']},"
                f"{record['Apparent_temperature']},"
                f"{record['Precipitation_probability']},"
                f"{record['Humidity']},"
                f"{record['Wind_speed']}\n"
            )
    print(f"  Exported {len(all_records)} forecast rows → {csv_path}")


def log_run_pipeline(results, locations):
    """Append a summary log entry after each pipeline run."""
    os.makedirs("data", exist_ok=True)
    with open("data/pipeline.log", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Pipeline run — {len(results)}/{len(locations)} cities processed successfully.\n")
        for record in results:
            f.write(
                f"    {record['Location']} | Apparent Temp: {record['Apparent_temperature']}° | Humidity: {record['Humidity']}% | Precip: {record['Precipitation_probability']}%\n"
            )
    print(f"Run logged → data/pipeline.log")


def run_pipeline(config_path="config.json"):
    """Iterates over all locations defined in config.json."""
    config = load_config(config_path)
    locations = config["locations"]
    units = config["units"]

    print(f"DataBridge V2 — Loading weather for {len(locations)} location(s)...\n")

    results = []
    all_forecast_rows = []

    for loc in locations:
        name = loc["name"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        print(f"[{name}]")

        raw_data = fetch_weather_data(lat, lon, units)
        if raw_data:
            records = transform_data(raw_data, name)
            for r in records:
                load_data(r)

            all_forecast_rows.extend(records)

            if records:
                results.append(records[0])
        else:
            print(f"  Skipping {name} due to fetch error.")


    print(f"\nPipeline complete. {len(results)} location(s) processed successfully.")
    export_to_csv(all_forecast_rows)
    log_run_pipeline(results, locations)

    return all_forecast_rows


if __name__ == "__main__":
    print("Initiating Program...")
    run_pipeline()
    print("Program complete.")