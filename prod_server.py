"""
Production server script for Windows deployment
Uses Waitress (Windows-compatible WSGI server)
"""
import os
import sys
from waitress import serve
from smartcity.wsgi import application

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting SmartCity EMS production server on port {port}...")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    
    serve(
        application,
        host='0.0.0.0',
        port=port,
        threads=4,  # Adjust based on your server capacity
        url_scheme='http',  # Change to 'https' if using SSL
        channel_timeout=120,
        cleanup_interval=30,
        connection_limit=1000,
    )