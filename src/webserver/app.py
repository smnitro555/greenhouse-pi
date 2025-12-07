"""
Greenhouse Webserver Application

Main Flask application entry point for the greenhouse monitoring and control interface.
Runs separately from greenhouse_manager.py on the Raspberry Pi.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import request, Response

# Add parent directory to path to import greenhouse modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from greenhouse_manager.greenhouse_data_logger import GreenhouseDataLogger


def create_app(config=None):
    """
    Application factory for creating Flask app.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production'),
        LOG_DIRECTORY='data/logs',
        IMAGE_DIRECTORY='data/images',
        # Basic auth credentials (in production, load from config file)
        BASIC_AUTH_USERNAME=os.environ.get('GREENHOUSE_USERNAME', 'admin'),
        BASIC_AUTH_PASSWORD=os.environ.get('GREENHOUSE_PASSWORD', 'greenhouse'),
    )

    # Apply custom config if provided
    if config:
        app.config.update(config)

    # Initialize data logger
    data_logger = GreenhouseDataLogger(
        log_directory=app.config['LOG_DIRECTORY'],
        log_format='parquet'
    )

    def check_auth(username, password):
        """
        Check if username/password combination is valid.

        Args:
            username: Provided username
            password: Provided password

        Returns:
            True if authentication is valid
        """
        return (username == app.config['BASIC_AUTH_USERNAME'] and
                password == app.config['BASIC_AUTH_PASSWORD'])

    def authenticate():
        """Send a 401 response to trigger browser basic auth."""
        return Response(
            'Authentication required. Please provide valid credentials.',
            401,
            {'WWW-Authenticate': 'Basic realm="Greenhouse Monitor"'}
        )

    def requires_auth(f):
        """
        Decorator for routes that require authentication.

        Usage:
            @app.route('/protected')
            @requires_auth
            def protected_route():
                return "This is protected"
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated

    # Main dashboard route
    @app.route('/')
    @requires_auth
    def index():
        """Main dashboard page with Plotly charts and image slideshow."""
        return render_template('index.html')

    # Register API blueprint
    from webserver.api import api_bp
    api_bp.data_logger = data_logger  # Attach data logger to blueprint
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Health check endpoint (no auth required)
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'service': 'greenhouse-webserver',
            'version': '0.1.0'
        })

    return app


def main():
    """
    Main entry point for running the Flask webserver.
    """
    app = create_app()

    # Get configuration from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"Starting Greenhouse Webserver on {host}:{port}")
    print(f"Access the dashboard at: http://{host}:{port}")
    print(f"Default credentials: admin / greenhouse")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
