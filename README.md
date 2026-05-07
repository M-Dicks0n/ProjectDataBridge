
# DataBridge: Weather Data ETL Pipeline
Project DataBridge started as a simple weather scraping application and has since been expanded into a multi-location ETL (Extract, Transform, Load) pipeline. V2 (technically my still V0.2) adds richer meteorological metrics and a CSV export layer designed to feed into Ensemble, a companion R-based wardrobe recommendation model.


### Core Features:
Automated Extraction for multiple locations:Pulls current weather data for multiple locations defined in config.json, replacing the original single hardcoded endpoint.
Expanded Metrics: Captures temperature, wind speed, apparent temperature (real feel), precipitation probability, and humidity.
Data Transformation: Handles complex JSON payloads, converting raw API responses into standardized formats.
Unit Conversion: Integrated logic for converting meteorological units (e.g., Temperature, Wind Speed (potenally real feel)) to meet specific project requirements.
Modular Architecture: Designed as a "standalone" application that has a .csv, .log. and db file for other programs. 
Run Logging: Writes a plain-text log summarizing each pipeline execution for traceability.


### Technical Stack:
Language: Python 3.x
API: Open-Meteo (free, no API key required)
Storage: sqlite3
Key Libraries: requests (for API handling), json (for parsing), sqlite2, os


### Prerequisites:
git clone https://github.com/M-Dicks0n/ProjectDataBridge.git
cd DataBridge


### Installation:
pip install -r requirements.txt


## Usage:
python DataBridge.py


## Initialize the pipeline:
pipeline = WeatherPipeline()
data = pipeline.run()
print(data)


##### Related Projects:
Ensemble — R-based ML wardrobe recommender that ingests DataBridge output.
