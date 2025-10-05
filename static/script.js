class WeatherApp {
    constructor() {
        this.tempChart = null;
        this.precipChart = null;
        this.currentData = null;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeWeather();
        });
        
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadData();
        });
    }
    
    async analyzeWeather() {
        const lat = parseFloat(document.getElementById('lat').value);
        const lon = parseFloat(document.getElementById('lon').value);
        const userType = document.getElementById('userType').value;
        const predictionDays = document.getElementById('predictionDays').value;
        
        if (isNaN(lat) || isNaN(lon)) {
            this.showError('Please enter valid coordinates');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/weather-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lat: lat,
                    lon: lon,
                    user_type: userType,
                    prediction_days: predictionDays
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentData = data;
                this.displayResults(data);
            } else {
                this.showError(data.error || 'Analysis failed');
            }
            
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    displayResults(data) {
        this.hideLoading();
        this.hideError();
        
        document.getElementById('results').style.display = 'block';
        
        // Display location info
        document.getElementById('locationInfo').innerHTML = `
            <p>Location: ${data.location.lat}°N, ${data.location.lon}°E</p>
            <p>Last updated: ${new Date(data.last_updated).toLocaleString()}</p>
        `;
        
        // Display climate normals
        this.displayClimateNormals(data.climate_normals);
        
        // Display predictions with charts
        this.displayPredictions(data.predictions);
        
        // Display seasonal forecast
        this.displaySeasonalForecast(data.seasonal_forecast);
        
        // Display user advice
        this.displayUserAdvice(data.user_advice, data.user_type);
    }
    
    displayClimateNormals(normals) {
        const normalsGrid = document.getElementById('normalsGrid');
        normalsGrid.innerHTML = `
            <div class="normal-card">
                <h4>Average Temperature</h4>
                <p>${normals.avg_temperature}°C</p>
            </div>
            <div class="normal-card">
                <h4>Average Precipitation</h4>
                <p>${normals.avg_precipitation} mm/day</p>
            </div>
            <div class="normal-card">
                <h4>Rainy Days</h4>
                <p>${normals.precipitation_days} days/year</p>
            </div>
            <div class="normal-card">
                <h4>Wind Speed</h4>
                <p>${normals.avg_wind_speed} m/s</p>
            </div>
        `;
    }
    
    displayPredictions(predictions) {
        const dates = predictions.map(p => new Date(p.date).toLocaleDateString());
        const temperatures = predictions.map(p => p.temperature);
        const precipitation = predictions.map(p => p.precipitation);
        
        // Create temperature chart
        this.createTemperatureChart(dates, temperatures);
        
        // Create precipitation chart
        this.createPrecipitationChart(dates, precipitation);
    }
    
    createTemperatureChart(dates, temperatures) {
        const ctx = document.getElementById('tempChart').getContext('2d');
        
        if (this.tempChart) {
            this.tempChart.destroy();
        }
        
        this.tempChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: temperatures,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Temperature Forecast'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    }
                }
            }
        });
    }
    
    createPrecipitationChart(dates, precipitation) {
        const ctx = document.getElementById('precipChart').getContext('2d');
        
        if (this.precipChart) {
            this.precipChart.destroy();
        }
        
        this.precipChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Precipitation (mm)',
                    data: precipitation,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: '#3498db',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Precipitation Forecast'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Precipitation (mm)'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    displaySeasonalForecast(seasonal) {
        const seasonalGrid = document.getElementById('seasonalGrid');
        let html = '';
        
        for (const [season, data] of Object.entries(seasonal)) {
            html += `
                <div class="seasonal-card">
                    <h4>${season}</h4>
                    <p>Avg Temp: ${data.avg_temperature}°C</p>
                    <p>Total Rain: ${data.total_precipitation} mm</p>
                    <p>Rainy Days: ${data.days_with_rain}</p>
                    <p>Max Temp: ${data.max_temperature}°C</p>
                    <p>Min Temp: ${data.min_temperature}°C</p>
                </div>
            `;
        }
        
        seasonalGrid.innerHTML = html;
    }
    
    displayUserAdvice(advice, userType) {
        const adviceContent = document.getElementById('adviceContent');
        let html = '';
        
        if (advice.immediate && advice.immediate.length > 0) {
            html += '<div class="advice-category"><h4>Immediate Actions</h4>';
            advice.immediate.forEach(item => {
                html += `<div class="advice-item">${item}</div>`;
            });
            html += '</div>';
        }
        
        if (advice.seasonal && advice.seasonal.length > 0) {
            html += '<div class="advice-category"><h4>Seasonal Planning</h4>';
            advice.seasonal.forEach(item => {
                html += `<div class="advice-item">${item}</div>`;
            });
            html += '</div>';
        }
        
        if (!html) {
            html = '<p>No specific advice for current conditions.</p>';
        }
        
        adviceContent.innerHTML = html;
    }
    
    downloadData() {
        if (!this.currentData) {
            alert('No data available to download');
            return;
        }
        
        const dataStr = JSON.stringify(this.currentData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `nasa_weather_data_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
    
    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('results').style.display = 'none';
        document.getElementById('error').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }
    
    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('error').style.display = 'block';
        document.getElementById('loading').style.display = 'none';
        document.getElementById('results').style.display = 'none';
    }
    
    hideError() {
        document.getElementById('error').style.display = 'none';
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new WeatherApp();
});