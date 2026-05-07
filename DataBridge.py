import requests
import json
import sqlite3
import os

def load_config(config="config.json"):
    #load location and unit settings from cofig.json
    with open(config, "r") as f:
        return json.load(f)

def fetch_weather_data(latitude, longitude, units):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current_weather=true"
        f"&hourly=apparent_temperature,precipitation_probability,relativehumidity_2m"
        f"&temperature_unit={units['temperature']}"
        f"&wind_speed_unit={units['wind_speed']}"
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
    """Parse the API response into a clean, structured record."""
    print(f"    Processing data for {location_name}...")

    current_node = raw_json.get("current_weather", {})
    clean_temp = float(current_node.get("temperature", 0.0))
    clean_wind = float(current_node.get("windspeed", 0.0))
    raw_time = current_node.get("time", "2020-01-01T00:00:00Z")
    clean_time = raw_time.replace("T", " ")
    # Find the hourly index that matches the current hour
    current_hour = raw_time[:13]  # e.g. "2026-05-06T18"
    hourly_times = raw_json.get("hourly", {}).get("time", [])
    hourly_index = next(
        (i for i, t in enumerate(hourly_times) if t.startswith(current_hour)), 0
    )

    # Extract new metrics at the matched index
    apparent_temp = float(raw_json["hourly"]["apparent_temperature"][hourly_index])
    precip_prob = int(raw_json["hourly"]["precipitation_probability"][hourly_index])
    humidity = int(raw_json["hourly"]["relativehumidity_2m"][hourly_index])

    transformed_data = {
        "Location": location_name,
        "Time": clean_time,
        "Temperature": clean_temp,
        "Wind_speed": clean_wind,
        "Apparent_temperature": apparent_temp,
        "Precipitation_probability": precip_prob,
        "Humidity": humidity,
    }
    return transformed_data


def load_data(transformed_data):
    """Insert a single weather record into the SQLite database."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/weather_data.db")
    cursor = conn.cursor()

    create_table = """
                   CREATE TABLE IF NOT EXISTS weather_log
                   (
                       id                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       location                  TEXT NOT NULL,
                       timestamp                 TEXT NOT NULL,
                       temperature               REAL,
                       wind_speed                REAL,
                       apparent_temperature      REAL,
                       precipitation_probability INTEGER,
                       humidity                  INTEGER
                   );
                   """
    cursor.execute(create_table)

    insert_sql = """
                 INSERT INTO weather_log (location, timestamp, temperature, wind_speed,apparent_temperature, precipitation_probability, humidity)
                 VALUES (?, ?, ?, ?, ?, ?, ?);
                 """
    data_tuple = (
        transformed_data.get("Location"),
        transformed_data.get("Time"),
        transformed_data.get("Temperature"),
        transformed_data.get("Wind_speed"),
        transformed_data.get("Apparent_temperature"),
        transformed_data.get("Precipitation_probability"),
        transformed_data.get("Humidity"),
    )
    cursor.execute(insert_sql, data_tuple)
    conn.commit()
    conn.close()
    print(f"    Logged to database.")

def export_to_csv(db_path='data/weather_data.db', csv_path='data/ensemble_input.csv'):
    """Export the data/record per location to a CSV file for later use(project ensemble)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = """
            SELECT location, timestamp, temperature, wind_speed,apparent_temperature, precipitation_probability, humidity
            FROM weather_log
            WHERE id IN (
                SELECT MAX(id) FROM weather_log GROUP BY location
            )
            ORDER BY location;
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    os.makedirs('data', exist_ok=True)
    with open(csv_path, 'w', newline='') as f:
        f.write("location,timestamp,temperature,wind_speed,apparent_temperature,precipitation_probability,humidity\n")
        for row in rows:
            f.write(",".join(str(val) for val in row) + "\n")
    print(f"    Data exported to ->{csv_path}")

def run_pipeline(config_path="config.json"):
    """
     Iterates over all locations defined in config.json
    """
    config = load_config(config_path)
    locations = config["locations"]
    units = config["units"]

    print(f"DataBridge V2 — Loading weather for {len(locations)} location(s)...\n")

    results = []
    for loc in locations:
        name = loc["name"]
        lat = loc["latitude"]
        lon = loc["longitude"]

        print(f"[{name}]")
        raw_data = fetch_weather_data(lat, lon, units)

        if raw_data:
            clean_data = transform_data(raw_data, name)
            print(json.dumps(clean_data, indent=4))
            load_data(clean_data)
            results.append(clean_data)
        else:
            print(f"    Skipping {name} due to fetch error.")

        print()

    print(f"Pipeline complete. {len(results)}/{len(locations)} location(s) processed successfully.")
    export_to_csv()
    log_run_pipeline(results, locations)
    return results

def log_run_pipeline(results, locations):
    """Append a summary log entry after each pipeline run."""
    os.makedirs("data", exist_ok=True)
    with open("data/pipeline.log", "a") as f:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Pipeline run — {len(results)}/{len(locations)} cities processed successfully.\n")
        for record in results:
            f.write(
                f"    {record['Location']} | Temp: {record['Temperature']}°F | Humidity: {record['Humidity']}% | Precip: {record['Precipitation_probability']}%\n")
    print(f"Run logged → data/pipeline.log")

if __name__ == "__main__":
    print("Initiating Program...")
    run_pipeline()