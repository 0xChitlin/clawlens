# Dashboard Component Template

For creating interactive visualizations and dashboards. Based on patterns from weather-dashboard and the OpenClaw observability dashboard.

## Template Files

### SKILL.md
```markdown
---
name: your-dashboard
description: Interactive dashboard with canvas visualization for [specific domain]. Extends [base-skill] with UI components.
---

# Your Dashboard

Interactive visualization dashboard for [domain]. Provides real-time monitoring, historical views, and interactive controls.

## Features

- 📊 Real-time data visualization
- 🎛️ Interactive controls and filters
- 📱 Responsive design (desktop/mobile)
- 🔄 Auto-refresh capabilities
- 📥 Export functionality (PNG, PDF, CSV)

## Quick Start

```bash
# Start dashboard server
python3 dashboard.py --port 8900

# Visit: http://localhost:8900
```

## Requirements

- `python3` with Flask, matplotlib, plotly (or similar)
- Data source (API, files, database)
- Modern web browser with JavaScript enabled

## Configuration

Set via environment variables or config file:

```bash
export DASHBOARD_PORT=8900
export DATA_SOURCE="api"          # api|file|database
export REFRESH_INTERVAL=60        # seconds
export ENABLE_EXPORT=true
```

## Components

### Data Panel
- Current status indicators
- Key metrics and KPIs  
- Trend indicators (↑↓)

### Chart Panel
- Time series visualizations
- Bar charts, pie charts, heatmaps
- Interactive zoom and filtering

### Control Panel
- Time range selector
- Filter controls
- Export buttons
- Refresh controls

## API Endpoints

```
GET  /api/data              # Current dataset
GET  /api/data/history      # Historical data  
GET  /api/status            # System status
POST /api/export            # Generate export
```

## Customization

Modify `dashboard.py` to:
- Add new chart types
- Customize styling/themes
- Add authentication
- Integrate with different data sources

## Mobile Responsiveness

Dashboard adapts to screen size:
- Desktop: Multi-column layout with detailed charts
- Tablet: Stacked layout with scrolling
- Mobile: Essential metrics only, simplified navigation
```

### dashboard.py
```python
#!/usr/bin/env python3
"""
Interactive Dashboard Template
Usage: python3 dashboard.py [--port PORT] [--debug]
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

app = Flask(__name__)

# Configuration
CONFIG = {
    'port': int(os.environ.get('DASHBOARD_PORT', 8900)),
    'debug': os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
    'data_source': os.environ.get('DATA_SOURCE', 'mock'),
    'refresh_interval': int(os.environ.get('REFRESH_INTERVAL', 60)),
    'enable_export': os.environ.get('ENABLE_EXPORT', 'true').lower() == 'true'
}

class DataProvider:
    """Handle data fetching from various sources"""
    
    def __init__(self, source_type='mock'):
        self.source_type = source_type
        
    def get_current_data(self):
        """Get current dataset"""
        if self.source_type == 'mock':
            return self._generate_mock_data()
        elif self.source_type == 'api':
            return self._fetch_from_api()
        elif self.source_type == 'file':
            return self._load_from_file()
        else:
            raise ValueError(f"Unknown data source: {self.source_type}")
    
    def get_historical_data(self, hours=24):
        """Get historical data for specified time range"""
        # Generate time series data
        now = datetime.now()
        timestamps = [now - timedelta(minutes=x*5) for x in range(hours*12)]
        
        return [{
            'timestamp': ts.isoformat(),
            'value': 50 + (hash(str(ts)) % 100),  # Mock data
            'status': 'normal' if hash(str(ts)) % 10 < 8 else 'warning'
        } for ts in timestamps]
    
    def _generate_mock_data(self):
        """Generate mock data for testing"""
        return {
            'current_value': 75,
            'status': 'normal',
            'trend': 'up',
            'metrics': {
                'total_requests': 1234,
                'error_rate': 2.1,
                'avg_response_time': 145,
                'active_users': 89
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def _fetch_from_api(self):
        """Fetch data from external API"""
        # Implement API integration
        import requests
        try:
            response = requests.get('https://api.example.com/data', timeout=5)
            return response.json()
        except requests.RequestException:
            return self._generate_mock_data()  # Fallback
    
    def _load_from_file(self):
        """Load data from local file"""
        try:
            with open('data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._generate_mock_data()

# Initialize data provider
data_provider = DataProvider(CONFIG['data_source'])

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html', config=CONFIG)

@app.route('/api/data')
def api_data():
    """Get current data"""
    try:
        data = data_provider.get_current_data()
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/history')
def api_history():
    """Get historical data"""
    hours = request.args.get('hours', 24, type=int)
    try:
        data = data_provider.get_historical_data(hours)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chart/<chart_type>')
def api_chart(chart_type):
    """Generate chart data"""
    try:
        if chart_type == 'timeseries':
            return generate_timeseries_chart()
        elif chart_type == 'metrics':
            return generate_metrics_chart()
        else:
            return jsonify({'error': 'Unknown chart type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_timeseries_chart():
    """Generate time series chart"""
    historical = data_provider.get_historical_data(24)
    
    timestamps = [item['timestamp'] for item in historical]
    values = [item['value'] for item in historical]
    
    trace = go.Scatter(
        x=timestamps,
        y=values,
        mode='lines+markers',
        name='Value',
        line=dict(color='#3b82f6', width=2)
    )
    
    layout = go.Layout(
        title='24 Hour Trend',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Value'),
        template='plotly_white',
        height=300
    )
    
    figure = go.Figure(data=[trace], layout=layout)
    return jsonify(plotly.utils.PlotlyJSONEncoder().encode(figure))

def generate_metrics_chart():
    """Generate metrics overview chart"""
    data = data_provider.get_current_data()
    metrics = data['metrics']
    
    labels = list(metrics.keys())
    values = list(metrics.values())
    
    trace = go.Bar(
        x=labels,
        y=values,
        marker=dict(color=['#10b981', '#f59e0b', '#ef4444', '#6366f1'])
    )
    
    layout = go.Layout(
        title='Current Metrics',
        template='plotly_white',
        height=300
    )
    
    figure = go.Figure(data=[trace], layout=layout)
    return jsonify(plotly.utils.PlotlyJSONEncoder().encode(figure))

@app.route('/api/export')
def api_export():
    """Export data in various formats"""
    format_type = request.args.get('format', 'json')
    
    try:
        data = data_provider.get_current_data()
        historical = data_provider.get_historical_data(24)
        
        export_data = {
            'current': data,
            'historical': historical,
            'exported_at': datetime.now().isoformat()
        }
        
        if format_type == 'json':
            return jsonify(export_data)
        elif format_type == 'csv':
            # Convert to CSV and return as file
            df = pd.DataFrame(historical)
            csv_file = '/tmp/export.csv'
            df.to_csv(csv_file, index=False)
            return send_file(csv_file, as_attachment=True, attachment_filename='data.csv')
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Template content for dashboard.html
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .metric-card { transition: transform 0.2s; }
        .metric-card:hover { transform: translateY(-2px); }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">Dashboard</h1>
        
        <!-- Status Bar -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                <h3 class="text-sm text-gray-500 mb-2">Total Requests</h3>
                <p class="text-2xl font-bold" id="metric-requests">-</p>
            </div>
            <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                <h3 class="text-sm text-gray-500 mb-2">Error Rate</h3>
                <p class="text-2xl font-bold" id="metric-errors">-%</p>
            </div>
            <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                <h3 class="text-sm text-gray-500 mb-2">Response Time</h3>
                <p class="text-2xl font-bold" id="metric-response">-ms</p>
            </div>
            <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                <h3 class="text-sm text-gray-500 mb-2">Active Users</h3>
                <p class="text-2xl font-bold" id="metric-users">-</p>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-white p-6 rounded-lg shadow-md">
                <div id="timeseries-chart"></div>
            </div>
            <div class="bg-white p-6 rounded-lg shadow-md">
                <div id="metrics-chart"></div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="mt-8 flex gap-4">
            <button onclick="refreshData()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                Refresh
            </button>
            <button onclick="exportData('json')" class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                Export JSON
            </button>
            <button onclick="exportData('csv')" class="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
                Export CSV
            </button>
        </div>
    </div>
    
    <script>
        // Auto-refresh every interval
        const refreshInterval = {{ config.refresh_interval * 1000 }};
        
        function updateMetrics(data) {
            document.getElementById('metric-requests').textContent = data.metrics.total_requests;
            document.getElementById('metric-errors').textContent = data.metrics.error_rate + '%';
            document.getElementById('metric-response').textContent = data.metrics.avg_response_time + 'ms';
            document.getElementById('metric-users').textContent = data.metrics.active_users;
        }
        
        async function refreshData() {
            try {
                const response = await fetch('/api/data');
                const result = await response.json();
                if (result.status === 'success') {
                    updateMetrics(result.data);
                    refreshCharts();
                }
            } catch (error) {
                console.error('Failed to refresh data:', error);
            }
        }
        
        async function refreshCharts() {
            try {
                // Time series chart
                const tsResponse = await fetch('/api/chart/timeseries');
                const tsData = await tsResponse.json();
                Plotly.newPlot('timeseries-chart', tsData.data, tsData.layout);
                
                // Metrics chart
                const metricsResponse = await fetch('/api/chart/metrics');
                const metricsData = await metricsResponse.json();
                Plotly.newPlot('metrics-chart', metricsData.data, metricsData.layout);
            } catch (error) {
                console.error('Failed to refresh charts:', error);
            }
        }
        
        function exportData(format) {
            window.open(`/api/export?format=${format}`, '_blank');
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh
        setInterval(refreshData, refreshInterval);
    </script>
</body>
</html>
'''

def create_template_file():
    """Create dashboard template file if it doesn't exist"""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    template_path = os.path.join(template_dir, 'dashboard.html')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write(DASHBOARD_TEMPLATE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start dashboard server')
    parser.add_argument('--port', type=int, default=CONFIG['port'], help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Create template file
    create_template_file()
    
    print(f"Starting dashboard on http://localhost:{args.port}")
    print(f"Data source: {CONFIG['data_source']}")
    print(f"Refresh interval: {CONFIG['refresh_interval']}s")
    
    app.run(host='0.0.0.0', port=args.port, debug=args.debug or CONFIG['debug'])
```

## Customization Checklist

- [ ] Define data schema and sources for your domain
- [ ] Choose visualization library (Plotly, D3.js, Chart.js, etc.)
- [ ] Design responsive layout for your screen targets
- [ ] Add authentication/authorization if needed
- [ ] Implement data export in required formats
- [ ] Add error handling and graceful degradation
- [ ] Configure auto-refresh intervals appropriately
- [ ] Add mobile-optimized views
- [ ] Test with real data volumes
- [ ] Document deployment and configuration options

## Dependencies

- **Python**: Flask, plotly, pandas, requests
- **Frontend**: Plotly.js, Tailwind CSS (or similar)
- **Optional**: Redis (caching), PostgreSQL (data storage)

## Deployment Options

1. **Development**: `python3 dashboard.py --debug`
2. **Production**: Use gunicorn + nginx reverse proxy
3. **Containerized**: Docker with health checks
4. **Systemd Service**: Auto-restart on system reboot

## Performance Considerations

1. **Caching**: Cache expensive data queries
2. **Pagination**: Limit data size for large datasets
3. **WebSockets**: Real-time updates without polling
4. **CDN**: Serve static assets from CDN
5. **Database Indexes**: Optimize query performance for historical data