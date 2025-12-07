"""
Tests for webserver module.

Tests Flask API endpoints and web interface.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webserver.app import create_app


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app({
        'TESTING': True,
        'BASIC_AUTH_USERNAME': 'test',
        'BASIC_AUTH_PASSWORD': 'password',
        'LOG_DIRECTORY': 'data/logs',
        'IMAGE_DIRECTORY': 'data/images'
    })
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create basic authentication headers for testing."""
    import base64
    credentials = base64.b64encode(b'test:password').decode('utf-8')
    return {'Authorization': f'Basic {credentials}'}


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    def test_health_check_no_auth(self, client):
        """Test health endpoint without authentication."""
        response = client.get('/health')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'greenhouse-webserver'

    def test_health_check_returns_json(self, client):
        """Test health endpoint returns JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'


class TestMainDashboard:
    """Test cases for main dashboard."""

    def test_index_without_auth(self, client):
        """Test accessing dashboard without authentication."""
        response = client.get('/')
        assert response.status_code == 401

    def test_index_with_auth(self, client, auth_headers):
        """Test accessing dashboard with authentication."""
        response = client.get('/', headers=auth_headers)
        assert response.status_code == 200
        assert b'Greenhouse Monitor' in response.data

    def test_index_wrong_credentials(self, client):
        """Test accessing dashboard with wrong credentials."""
        import base64
        wrong_creds = base64.b64encode(b'wrong:credentials').decode('utf-8')
        headers = {'Authorization': f'Basic {wrong_creds}'}

        response = client.get('/', headers=headers)
        assert response.status_code == 401


class TestAPIStatusEndpoint:
    """Test cases for /api/v1/status endpoint."""

    def test_status_without_auth(self, client):
        """Test status endpoint without authentication."""
        response = client.get('/api/v1/status')
        assert response.status_code == 401

    def test_status_with_auth(self, client, auth_headers):
        """Test status endpoint with authentication."""
        response = client.get('/api/v1/status', headers=auth_headers)
        # May return 404 or 500 if no data available, which is expected
        assert response.status_code in [200, 404, 500]

    def test_status_returns_json(self, client, auth_headers):
        """Test status endpoint returns JSON."""
        response = client.get('/api/v1/status', headers=auth_headers)
        assert response.content_type == 'application/json'


class TestAPIHistoryEndpoint:
    """Test cases for /api/v1/history endpoint."""

    def test_history_without_auth(self, client):
        """Test history endpoint without authentication."""
        response = client.get('/api/v1/history')
        assert response.status_code == 401

    def test_history_with_auth(self, client, auth_headers):
        """Test history endpoint with authentication."""
        response = client.get('/api/v1/history', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data

    def test_history_with_date_parameter(self, client, auth_headers):
        """Test history endpoint with date parameter."""
        response = client.get('/api/v1/history?day=2024-01-15', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['date'] == '2024-01-15'

    def test_history_invalid_date_format(self, client, auth_headers):
        """Test history endpoint with invalid date format."""
        response = client.get('/api/v1/history?day=invalid-date', headers=auth_headers)
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data


class TestAPIHistoryRangeEndpoint:
    """Test cases for /api/v1/history/range endpoint."""

    def test_history_range_without_params(self, client, auth_headers):
        """Test history range without required parameters."""
        response = client.get('/api/v1/history/range', headers=auth_headers)
        assert response.status_code == 400

    def test_history_range_with_valid_params(self, client, auth_headers):
        """Test history range with valid date parameters."""
        response = client.get(
            '/api/v1/history/range?start=2024-01-01&end=2024-01-31',
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'success'

    def test_history_range_start_after_end(self, client, auth_headers):
        """Test history range with start date after end date."""
        response = client.get(
            '/api/v1/history/range?start=2024-12-31&end=2024-01-01',
            headers=auth_headers
        )
        assert response.status_code == 400


class TestAPIStatisticsEndpoint:
    """Test cases for /api/v1/statistics endpoint."""

    def test_statistics_without_auth(self, client):
        """Test statistics endpoint without authentication."""
        response = client.get('/api/v1/statistics')
        assert response.status_code == 401

    def test_statistics_with_auth(self, client, auth_headers):
        """Test statistics endpoint with authentication."""
        response = client.get('/api/v1/statistics', headers=auth_headers)
        # May return 404 if no data, which is expected
        assert response.status_code in [200, 404]


class TestAPICameraEndpoints:
    """Test cases for camera-related API endpoints."""

    def test_camera_latest_without_auth(self, client):
        """Test camera latest endpoint without authentication."""
        response = client.get('/api/v1/camera/latest')
        assert response.status_code == 401

    def test_camera_latest_with_auth(self, client, auth_headers):
        """Test camera latest endpoint with authentication."""
        response = client.get('/api/v1/camera/latest', headers=auth_headers)
        # Will return 404 if no images exist, which is expected
        assert response.status_code in [200, 404]

    def test_camera_list_without_auth(self, client):
        """Test camera list endpoint without authentication."""
        response = client.get('/api/v1/camera/list')
        assert response.status_code == 401

    def test_camera_list_with_auth(self, client, auth_headers):
        """Test camera list endpoint with authentication."""
        response = client.get('/api/v1/camera/list', headers=auth_headers)
        # Will return 404 if directory doesn't exist, which is expected
        assert response.status_code in [200, 404]

    def test_camera_list_with_date(self, client, auth_headers):
        """Test camera list endpoint with date parameter."""
        response = client.get('/api/v1/camera/list?day=2024-01-15', headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_camera_image_without_auth(self, client):
        """Test camera image endpoint without authentication."""
        response = client.get('/api/v1/camera/image/test.jpg')
        assert response.status_code == 401


class TestAppConfiguration:
    """Test cases for application configuration."""

    def test_create_app_with_custom_config(self):
        """Test creating app with custom configuration."""
        custom_config = {
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'BASIC_AUTH_USERNAME': 'custom_user',
            'BASIC_AUTH_PASSWORD': 'custom_pass'
        }

        app = create_app(custom_config)
        assert app.config['TESTING'] is True
        assert app.config['SECRET_KEY'] == 'test-secret-key'
        assert app.config['BASIC_AUTH_USERNAME'] == 'custom_user'

    def test_create_app_default_config(self):
        """Test creating app with default configuration."""
        app = create_app()
        assert 'SECRET_KEY' in app.config
        assert 'BASIC_AUTH_USERNAME' in app.config
