from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json

from nasa_enhanced import EnhancedNASAWeather

app = Flask(__name__)
nasa_weather = EnhancedNASAWeather()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/geocode', methods=['POST'])
def geocode_location():
    """Geocode a location name to coordinates"""
    try:
        data = request.json
        location_name = data.get('location', '').strip()
        
        if not location_name:
            return jsonify({'success': False, 'error': 'Location name is required'})
        
        result = nasa_weather.geocode_location(location_name)
        
        if result:
            return jsonify({
                'success': True,
                'location': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Location not found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-predict', methods=['POST'])
def weather_predict():
    """Get weather predictions for a location"""
    try:
        data = request.json
        lat = float(data.get('lat', -1.2921))
        lon = float(data.get('lon', 36.8219))
        user_type = data.get('user_type', 'farmer')
        days = int(data.get('days', 365))
        
        print(f"Getting predictions for {lat}, {lon}...")
        
        predictions = nasa_weather.predict_weather(lat, lon, days)
        seasonal = nasa_weather.get_seasonal_summary(predictions)
        advice = nasa_weather.get_user_advice(user_type, predictions)
        
        response = {
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'predictions': predictions,
            'seasonal_forecast': seasonal,
            'user_advice': advice,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/specific-day', methods=['POST'])
def specific_day_weather():
    """Get weather data for a specific day"""
    try:
        data = request.json
        lat = float(data.get('lat', -1.2921))
        lon = float(data.get('lon', 36.8219))
        target_date = data.get('date')
        user_type = data.get('user_type', 'farmer')
        
        if not target_date:
            return jsonify({'success': False, 'error': 'Date is required'})
        
        # Validate date format
        try:
            datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'})
        
        day_data = nasa_weather.get_specific_day_data(lat, lon, target_date)
        
        if day_data:
            # Get advice for this specific day
            predictions = nasa_weather.predict_weather(lat, lon, days=30)
            advice = nasa_weather.get_user_advice(user_type, predictions, specific_day_data=day_data)
            
            response = {
                'success': True,
                'location': {'lat': lat, 'lon': lon},
                'date': target_date,
                'data': day_data,
                'user_advice': advice,
                'generated_at': datetime.now().isoformat()
            }
            return jsonify(response)
        else:
            return jsonify({
                'success': False,
                'error': f'No data available for {target_date}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test')
def test_api():
    """Test endpoint"""
    try:
        predictions = nasa_weather.predict_weather(-1.2921, 36.8219, 7)
        return jsonify({
            'success': True,
            'message': 'API is working',
            'sample_predictions': predictions[:3]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Enhanced NASA Weather Predictor...")
    print("Visit http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)