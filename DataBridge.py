import requests
import json

def fetch_weather_data():
    # Example: Fetching current weather for New York City
    url = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&current_weather=true"

    try:
        response = requests.get(url)
        # Check if the request was successful
        response.raise_for_status()
        # Add your visual confirmation here!
        print("Status: 200 OK - Connection Successful!\n")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


if __name__ == "__main__":
    print("Initiating API connection...")
    weather_payload = fetch_weather_data()

    if weather_payload:
        # Format and print the payload if the fetch was successful
        formatted_json = json.dumps(weather_payload, indent=4)
        print(formatted_json)
    else:
        print("Pipeline failed to retrieve data.")