from flask import Flask, render_template, request
from geopy.geocoders import Nominatim
import xarray as xr
import datetime

app = Flask(__name__)

# NASA OPeNDAP dataset URLs — replace with real working ones later
DATASETS = {
    "temperature": "https://opendap.nccs.nasa.gov/dods/MERRA2/M2I1NXASM_5.12.4",
    "rainfall": "https://opendap.nccs.nasa.gov/dods/GPCP",
    "windspeed": "https://opendap.nccs.nasa.gov/dods/MERRA2/M2I3NPASM",
    "dust": "https://opendap.nccs.nasa.gov/dods/MERRA2/M2I3NPANA",
    "snowfall": "https://opendap.nccs.nasa.gov/dods/MERRA2/M2I1NXASM",
    "cloudcover": "https://opendap.nccs.nasa.gov/dods/MERRA2/M2I1NXASM",
}

def geocode_location(location_name):
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    return None, None

def fetch_weather_data(lat, lon, date):
    results = {}
    for var, url in DATASETS.items():
        try:
            ds = xr.open_dataset(url, decode_times=True)

            # Debug: print dataset variables
            print(f"Dataset for {var}: {ds}")

            # Attempt to fetch the closest data
            if var in ds.variables:
                value = ds[var].sel(lat=lat, lon=lon, method="nearest").sel(time=date, method="nearest").values
                results[var] = float(value) if value.size > 0 else None
            else:
                results[var] = None
        except Exception as e:
            results[var] = None
            print(f"Error fetching {var}: {e}")
    return results

def personalize_message(weather_data, preferences):
    messages = []

    try:
        temp = float(weather_data.get("temperature") or 0)
        if preferences.get("hot") and temp > 30:
            messages.append("Very hot day expected — consider staying hydrated.")
        if preferences.get("cold") and temp < 0:
            messages.append("Very cold day expected — dress warmly.")
    except Exception:
        messages.append("Temperature data unavailable.")

    try:
        rainfall = float(weather_data.get("rainfall") or 0)
        if rainfall > 10:
            messages.append("High precipitation — bring waterproof gear.")
    except Exception:
        messages.append("Rainfall data unavailable.")

    try:
        windspeed = float(weather_data.get("windspeed") or 0)
        if preferences.get("windy") and windspeed > 10:
            messages.append("Very windy day expected — caution outdoors.")
    except Exception:
        messages.append("Windspeed data unavailable.")

    try:
        snowfall = float(weather_data.get("snowfall") or 0)
        if preferences.get("snowy") and snowfall > 5:
            messages.append("Significant snowfall expected — enjoy the snow!")
    except Exception:
        messages.append("Snowfall data unavailable.")

    return messages

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        location = request.form.get("location")
        date_str = request.form.get("date")
        preferences = {
            "hot": "hot" in request.form,
            "cold": "cold" in request.form,
            "windy": "windy" in request.form,
            "snowy": "snowy" in request.form,
        }
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return render_template("index.html", error="Invalid date format.")

        lat, lon = geocode_location(location)
        if lat is None:
            return render_template("index.html", error="Location not found.")

        weather_data = fetch_weather_data(lat, lon, date)
        messages = personalize_message(weather_data, preferences)

        return render_template("results.html", location=location, date=date_str, data=weather_data, messages=messages)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
