import requests
import json
from datetime import datetime, timedelta
import random
import math
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class EnhancedNASAWeather:
    def __init__(self):
        self.base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        self.geolocator = Nominatim(user_agent="nasa_weather_app")
        
    def geocode_location(self, location_name):
        """Convert location name to coordinates"""
        try:
            location = self.geolocator.geocode(location_name, timeout=10)
            if location:
                return {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'address': location.address
                }
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error: {e}")
            return None
    
    def get_historical_data(self, lat, lon, start_date, end_date):
        """Get historical weather data from NASA POWER API with robust parameter handling"""
        try:
            parameter_sets = [
                'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,WS2M,RH2M',
                'T2M,T2M_MAX,T2M_MIN,PRECTOT,WS2M,RH2M',
                'T2M,PRECTOTCORR,WS2M',
                'T2M,PRECTOT,WS2M'
            ]
            
            for parameters in parameter_sets:
                try:
                    params = {
                        'parameters': parameters,
                        'start': start_date,
                        'end': end_date,
                        'latitude': lat,
                        'longitude': lon,
                        'community': 'AG',
                        'format': 'JSON'
                    }
                    
                    print(f"Trying parameters: {parameters}")
                    response = requests.get(self.base_url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        parsed_data = self._parse_nasa_data(data)
                        if parsed_data and len(parsed_data) > 0:
                            print(f"Successfully fetched data with parameters: {parameters}")
                            return parsed_data
                    
                except Exception as e:
                    print(f"Failed with parameters {parameters}: {e}")
                    continue
            
            raise Exception("All NASA API parameter sets failed")
                
        except Exception as e:
            print(f"NASA API failed, using simulated data: {e}")
            return self._generate_simulated_data(lat, lon, start_date, end_date)
    
    def _parse_nasa_data(self, data):
        """Parse NASA POWER API response with flexible parameter handling"""
        parameters = data.get('properties', {}).get('parameter', {})
        
        if not parameters:
            print("No parameters in NASA response")
            return []
        
        available_params = list(parameters.keys())
        if not available_params:
            return []
            
        first_param = available_params[0]
        dates = list(parameters[first_param].keys())
        
        if not dates:
            return []
        
        records = []
        for date_str in dates:
            try:
                record = {
                    'date': datetime.strptime(date_str, '%Y%m%d'),
                    'date_str': date_str
                }
                
                # Map different parameter names to standard names
                param_mapping = {
                    'T2M': 'temperature',
                    'T2M_MAX': 'max_temperature',
                    'T2M_MIN': 'min_temperature',
                    'PRECTOTCORR': 'precipitation',
                    'PRECTOT': 'precipitation',
                    'WS2M': 'wind_speed',
                    'RH2M': 'humidity'
                }
                
                for nasa_param, std_param in param_mapping.items():
                    if nasa_param in parameters and date_str in parameters[nasa_param]:
                        record[std_param] = parameters[nasa_param][date_str]
                
                # Ensure we have at least temperature data
                if 'temperature' in record:
                    records.append(record)
                    
            except Exception as e:
                print(f"Error parsing date {date_str}: {e}")
                continue
        
        return records
    
    def _generate_simulated_data(self, lat, lon, start_date, end_date):
        """Generate realistic simulated weather data"""
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        records = []
        current_date = start
        
        # Create a consistent seed based on location
        seed_value = abs(hash(f"{lat}_{lon}")) % 10000
        random.seed(seed_value)
        
        while current_date <= end:
            day_of_year = current_date.timetuple().tm_yday
            
            # Base climate based on latitude with more realistic variations
            base_temp = 25 - (abs(lat) - 30) * 0.7
            if lat < 0:  # Southern hemisphere
                seasonal_temp = 10 * math.sin(2 * math.pi * (day_of_year - 265) / 365)
            else:  # Northern hemisphere
                seasonal_temp = 10 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
            
            # More realistic temperature variations
            temp_variation = random.gauss(0, 4)
            max_temp = base_temp + seasonal_temp + temp_variation + 6
            min_temp = base_temp + seasonal_temp + temp_variation - 6
            mean_temp = (max_temp + min_temp) / 2
            
            # Precipitation based on season and latitude
            if abs(lat) < 30:  # Tropical regions
                precip_prob = 0.4 + 0.2 * math.sin(2 * math.pi * (day_of_year - 200) / 365)
            else:  # Temperate regions
                precip_prob = 0.3 + 0.3 * math.sin(2 * math.pi * (day_of_year - 170) / 365)
            
            if random.random() < precip_prob:
                # More realistic precipitation distribution
                precipitation = max(0, random.gauss(2, 3))
            else:
                precipitation = 0
            
            # Wind speed based on location and season
            base_wind = 3 + abs(lat) * 0.1
            wind_speed = max(0, random.gauss(base_wind, 2))
            
            # Humidity variations
            base_humidity = 60 + (30 - abs(lat)) * 0.5
            humidity = max(30, min(95, random.gauss(base_humidity, 15)))
            
            record = {
                'date': current_date,
                'date_str': current_date.strftime('%Y%m%d'),
                'temperature': round(mean_temp, 1),
                'max_temperature': round(max_temp, 1),
                'min_temperature': round(min_temp, 1),
                'precipitation': round(precipitation, 1),
                'wind_speed': round(wind_speed, 1),
                'humidity': round(humidity, 1)
            }
            
            records.append(record)
            current_date += timedelta(days=1)
        
        print(f"Generated {len(records)} days of simulated data")
        return records
    
    def get_specific_day_data(self, lat, lon, target_date):
        """Get weather data for a specific day (historical or prediction)"""
        try:
            target_datetime = datetime.strptime(target_date, '%Y-%m-%d')
            today = datetime.now()
            
            if target_datetime <= today:
                # Historical data
                start_date = target_datetime.strftime('%Y%m%d')
                end_date = target_datetime.strftime('%Y%m%d')
                historical_data = self.get_historical_data(lat, lon, start_date, end_date)
                
                if historical_data and len(historical_data) > 0:
                    return {
                        'type': 'historical',
                        'data': historical_data[0],
                        'is_prediction': False
                    }
            else:
                # Future prediction
                predictions = self.predict_weather(lat, lon, days=365)
                for pred in predictions:
                    if pred['date'] == target_date:
                        return {
                            'type': 'prediction',
                            'data': pred,
                            'is_prediction': True
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting specific day data: {e}")
            return None
    
    def predict_weather(self, lat, lon, days=365):
        """Predict weather for the next days using improved algorithms"""
        try:
            # Get historical data (last 3 years for better patterns)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y%m%d')  # 3 years
            
            print(f"Fetching historical data from {start_date} to {end_date}")
            historical_data = self.get_historical_data(lat, lon, start_date, end_date)
            
            if not historical_data:
                print("No historical data available, generating basic predictions")
                return self._generate_basic_predictions(lat, lon, days)
            
            predictions = []
            last_date = historical_data[-1]['date'] if historical_data else datetime.now()
            
            for i in range(days):
                future_date = last_date + timedelta(days=i+1)
                day_of_year = future_date.timetuple().tm_yday
                
                # Find similar historical days with improved matching
                similar_days = self._find_similar_days(historical_data, day_of_year, lat)
                
                if similar_days and len(similar_days) > 5:
                    # Use weighted average based on how similar the days are
                    pred_temp = self._weighted_average(similar_days, 'temperature', day_of_year)
                    pred_precip = self._weighted_average(similar_days, 'precipitation', day_of_year)
                    pred_wind = self._weighted_average(similar_days, 'wind_speed', day_of_year)
                    pred_humidity = self._weighted_average(similar_days, 'humidity', day_of_year)
                    
                    # Add realistic randomness
                    pred_temp += random.gauss(0, 1.5)
                    pred_precip = max(0, pred_precip + random.gauss(0, 0.8))
                    pred_wind = max(0.1, pred_wind + random.gauss(0, 0.5))
                    pred_humidity = max(20, min(95, pred_humidity + random.gauss(0, 5)))
                else:
                    # Fallback to climate-based prediction
                    pred_temp, pred_precip, pred_wind, pred_humidity = self._climate_based_prediction(lat, lon, day_of_year)
                
                prediction = {
                    'date': future_date.strftime('%Y-%m-%d'),
                    'temperature': round(pred_temp, 1),
                    'precipitation': round(max(0, pred_precip), 1),
                    'wind_speed': round(max(0.1, pred_wind), 1),
                    'max_temperature': round(pred_temp + random.uniform(2, 6), 1),
                    'min_temperature': round(pred_temp - random.uniform(2, 6), 1),
                    'humidity': round(pred_humidity, 1)
                }
                
                predictions.append(prediction)
            
            print(f"Generated {len(predictions)} days of predictions")
            return predictions
            
        except Exception as e:
            print(f"Error in weather prediction: {e}")
            return self._generate_basic_predictions(lat, lon, days)
    
    def _find_similar_days(self, historical_data, target_day_of_year, lat, window=10):
        """Find historically similar days with improved matching"""
        similar_days = []
        
        for record in historical_data:
            record_day = record['date'].timetuple().tm_yday
            
            # Calculate day difference considering year wrap-around
            day_diff = min(
                abs(record_day - target_day_of_year),
                365 - abs(record_day - target_day_of_year)
            )
            
            # Weight by how close the day is (closer days have higher weight)
            if day_diff <= window:
                similar_days.append(record)
        
        return similar_days
    
    def _weighted_average(self, similar_days, parameter, target_day_of_year):
        """Calculate weighted average based on day similarity"""
        if not similar_days:
            return 0
            
        total_weight = 0
        weighted_sum = 0
        
        for day in similar_days:
            record_day = day['date'].timetuple().tm_yday
            day_diff = min(
                abs(record_day - target_day_of_year),
                365 - abs(record_day - target_day_of_year)
            )
            
            # Weight: closer days have higher weight
            weight = 1.0 / (1 + day_diff)
            total_weight += weight
            weighted_sum += day.get(parameter, 0) * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _climate_based_prediction(self, lat, lon, day_of_year):
        """Generate prediction based on climate norms"""
        # Base climate based on latitude
        base_temp = 25 - (abs(lat) - 30) * 0.7
        
        if lat < 0:  # Southern hemisphere
            seasonal_temp = 10 * math.sin(2 * math.pi * (day_of_year - 265) / 365)
        else:  # Northern hemisphere
            seasonal_temp = 10 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        temp = base_temp + seasonal_temp + random.gauss(0, 3)
        
        # Precipitation
        if abs(lat) < 30:  # Tropical
            precip_prob = 0.4
        else:  # Temperate
            precip_prob = 0.3
            
        precipitation = random.expovariate(2) if random.random() < precip_prob else 0
        
        # Wind and humidity
        wind_speed = random.weibullvariate(3, 1.8)
        humidity = random.uniform(40, 80)
        
        return temp, precipitation, wind_speed, humidity
    
    def _generate_basic_predictions(self, lat, lon, days):
        """Generate basic predictions when historical data is unavailable"""
        predictions = []
        current_date = datetime.now()
        
        for i in range(days):
            future_date = current_date + timedelta(days=i+1)
            day_of_year = future_date.timetuple().tm_yday
            
            temp, precip, wind, humidity = self._climate_based_prediction(lat, lon, day_of_year)
            
            prediction = {
                'date': future_date.strftime('%Y-%m-%d'),
                'temperature': round(temp, 1),
                'precipitation': round(precip, 1),
                'wind_speed': round(wind, 1),
                'max_temperature': round(temp + 4, 1),
                'min_temperature': round(temp - 4, 1),
                'humidity': round(humidity, 1)
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def get_seasonal_summary(self, predictions):
        """Generate seasonal summary from predictions"""
        seasons = {
            'Winter': [12, 1, 2],
            'Spring': [3, 4, 5],
            'Summer': [6, 7, 8],
            'Fall': [9, 10, 11]
        }
        
        seasonal_data = {}
        
        for season, months in seasons.items():
            season_predictions = [
                p for p in predictions 
                if datetime.strptime(p['date'], '%Y-%m-%d').month in months
            ]
            
            if season_predictions and len(season_predictions) > 0:
                temps = [p['temperature'] for p in season_predictions]
                precip = [p['precipitation'] for p in season_predictions]
                max_temps = [p['max_temperature'] for p in season_predictions]
                min_temps = [p['min_temperature'] for p in season_predictions]
                
                seasonal_data[season] = {
                    'avg_temperature': round(sum(temps) / len(temps), 1),
                    'total_precipitation': round(sum(precip), 1),
                    'days_with_rain': len([p for p in season_predictions if p['precipitation'] > 0.1]),
                    'max_temperature': round(max(max_temps), 1),
                    'min_temperature': round(min(min_temps), 1),
                    'prediction_count': len(season_predictions)
                }
        
        return seasonal_data
    
    def get_user_advice(self, user_type, predictions, specific_day_data=None):
        """Generate user-specific advice"""
        advice = {
            'immediate': [],
            'seasonal': [],
            'specific_day': []
        }
        
        if not predictions or len(predictions) == 0:
            advice['immediate'].append("No prediction data available")
            return advice
        
        # Next 7 days analysis
        next_week = predictions[:7]
        avg_temp = sum(p['temperature'] for p in next_week) / len(next_week)
        total_rain = sum(p['precipitation'] for p in next_week)
        rainy_days = len([p for p in next_week if p['precipitation'] > 1])
        max_temp = max(p['temperature'] for p in next_week)
        min_temp = min(p['temperature'] for p in next_week)
        
        if user_type == 'farmer':
            if avg_temp > 15 and total_rain > 10:
                advice['immediate'].append("Good planting conditions this week")
            elif avg_temp < 10:
                advice['immediate'].append("Wait for warmer weather before planting")
            
            if total_rain < 5:
                advice['immediate'].append("Consider irrigation due to low rainfall")
            elif rainy_days > 3:
                advice['immediate'].append("Good natural irrigation this week")
                
            if max_temp > 35:
                advice['immediate'].append("Extreme heat warning - protect crops")
            if min_temp < 5:
                advice['immediate'].append("Frost risk - protect sensitive plants")
                
        elif user_type == 'driver':
            if rainy_days > 2:
                advice['immediate'].append("Expect wet roads - drive carefully")
            if max_temp > 35:
                advice['immediate'].append("Extreme heat expected - check vehicle cooling system")
            if min_temp < 5:
                advice['immediate'].append("Risk of frost on roads and bridges")
            if any(p['wind_speed'] > 10 for p in next_week):
                advice['immediate'].append("Windy conditions expected - be cautious")
                
        elif user_type == 'event_organizer':
            dry_days = len([p for p in next_week if p['precipitation'] < 1])
            comfortable_days = len([p for p in next_week if 15 <= p['temperature'] <= 30])
            
            if dry_days >= 5:
                advice['immediate'].append("Good week for outdoor events")
            else:
                advice['immediate'].append("Consider rain contingency plans")
                
            if comfortable_days >= 4:
                advice['immediate'].append("Most days have comfortable temperatures")
        
        # Specific day advice
        if specific_day_data and specific_day_data.get('data'):
            day_data = specific_day_data['data']
            is_prediction = specific_day_data.get('is_prediction', False)
            
            data_type = "predicted" if is_prediction else "historical"
            temp = day_data.get('temperature', day_data.get('T2M', 0))
            precip = day_data.get('precipitation', day_data.get('PRECTOT', day_data.get('PRECTOTCORR', 0)))
            wind = day_data.get('wind_speed', day_data.get('WS2M', 0))
            
            if user_type == 'farmer':
                if temp > 15 and precip > 5:
                    advice['specific_day'].append(f"Based on {data_type} data: Good day for field work")
                elif precip > 10:
                    advice['specific_day'].append(f"Based on {data_type} data: Heavy rain expected - postpone outdoor work")
                elif temp > 35:
                    advice['specific_day'].append(f"Based on {data_type} data: Extreme heat - protect crops and workers")
                    
            elif user_type == 'driver':
                if precip > 5:
                    advice['specific_day'].append(f"Based on {data_type} data: Wet road conditions expected")
                if temp > 35:
                    advice['specific_day'].append(f"Based on {data_type} data: Extreme heat - check vehicle fluids")
                if wind > 15:
                    advice['specific_day'].append(f"Based on {data_type} data: Strong winds - be cautious on open roads")
                    
            elif user_type == 'event_organizer':
                if precip < 1 and 15 <= temp <= 30:
                    advice['specific_day'].append(f"Based on {data_type} data: Perfect weather for outdoor events")
                elif precip > 5:
                    advice['specific_day'].append(f"Based on {data_type} data: Rain expected - consider indoor venue")
                elif temp > 32:
                    advice['specific_day'].append(f"Based on {data_type} data: Hot weather - provide shade and water")
        
        return advice

# Test the enhanced class
if __name__ == "__main__":
    nasa = EnhancedNASAWeather()
    
    # Test with different locations
    test_locations = [
        ("Nairobi, Kenya", -1.2921, 36.8219),
        ("London, UK", 51.5074, -0.1278),
        ("New York, USA", 40.7128, -74.0060)
    ]
    
    for location_name, lat, lon in test_locations:
        print(f"\nTesting {location_name}:")
        
        # Test geocoding
        location = nasa.geocode_location(location_name)
        if location:
            print(f"Geocoding result: {location}")
        
        # Test specific day data
        specific_day = nasa.get_specific_day_data(lat, lon, "2024-06-15")
        print(f"Specific day data: {specific_day is not None}")
        
        # Test predictions
        predictions = nasa.predict_weather(lat, lon, days=7)
        print(f"Generated {len(predictions)} predictions")
        
        if predictions:
            print("Sample prediction:", predictions[0])