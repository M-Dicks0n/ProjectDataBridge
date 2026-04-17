import requests
import json


def fetch_weather_data():
    # Example: Fetching current weather for New York City
    url = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&current_weather=true&temperature_unit=fahrenheit&wind_speed_unit=mph"

    try:
        response = requests.get(url)
        response.raise_for_status()
        #  visual confirmation
        print("Status: 200 OK - Connection Successful!\n")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with Connection: {e}")
        return None


def transform_data(raw_json):
    print("Processing Data...")

    current_node = raw_json.get("current_weather", {})
    clean_temp = float(current_node.get("temperature", 0.0))
    ''' TODO add real feel
    #clean_feel = float(current_node.get("apparent_temperature",
                                        0.0))  
    '''
    clean_wind = float(current_node.get("windspeed", 0.0))
    raw_time = current_node.get("time", "2020-01-01T00:00:00Z")
    clean_time = raw_time.replace("T", " ")

    transformed_data = {
        "Time": clean_time,
        "Temperature": clean_temp,
        "Wind_speed": clean_wind,
    }
    return transformed_data


if __name__ == "__main__":
    print("Initiating Connection...")
    weather_data = fetch_weather_data()

    if weather_data:
        clean_data = transform_data(weather_data)
        print(json.dumps(clean_data, indent=4))
    else:
        print("Error Retrieving Data.")