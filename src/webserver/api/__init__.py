"""
Greenhouse API Module

REST API endpoints for accessing greenhouse data.
"""

import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file
from functools import wraps


# Create API blueprint
api_bp = Blueprint('api', __name__)

# Data logger will be attached by app.py
data_logger = None


def requires_auth(f):
    """
    Decorator for API routes that require authentication.
    Reuses the authentication from the main app.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, Response

        auth = request.authorization
        # Get auth check from current app config
        from flask import current_app
        username = current_app.config.get('BASIC_AUTH_USERNAME', 'admin')
        password = current_app.config.get('BASIC_AUTH_PASSWORD', 'greenhouse')

        if not auth or auth.username != username or auth.password != password:
            return Response(
                'Authentication required.',
                401,
                {'WWW-Authenticate': 'Basic realm="Greenhouse API"'}
            )
        return f(*args, **kwargs)
    return decorated


@api_bp.route('/status', methods=['GET'])
@requires_auth
def get_status():
    """
    GET /api/v1/status

    Returns the latest sensor readings and device states.

    Returns:
        JSON response with current greenhouse status
    """
    if data_logger is None:
        return jsonify({'error': 'Data logger not initialized'}), 500

    latest_reading = data_logger.get_latest_reading()

    if latest_reading is None:
        return jsonify({'error': 'No data available'}), 404

    # Convert timestamp to ISO format if it exists
    if 'timestamp' in latest_reading and latest_reading['timestamp']:
        latest_reading['timestamp'] = latest_reading['timestamp'].isoformat()

    return jsonify({
        'status': 'success',
        'data': latest_reading
    })


@api_bp.route('/history', methods=['GET'])
@requires_auth
def get_history():
    """
    GET /api/v1/history?day=YYYY-MM-DD

    Returns historical data for a given day.
    If no day is provided, returns data for today.

    Query Parameters:
        day: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        JSON response with historical data for the specified day
    """
    if data_logger is None:
        return jsonify({'error': 'Data logger not initialized'}), 500

    # Get date from query parameter or use today
    day_str = request.args.get('day')

    if day_str:
        try:
            date = datetime.strptime(day_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
    else:
        date = datetime.now()

    # Get data for the specified date
    df = data_logger.get_data_for_date(date)

    if df is None or df.empty:
        return jsonify({
            'status': 'success',
            'data': {
                'date': date.strftime('%Y-%m-%d'),
                'records': []
            }
        })

    # Convert DataFrame to list of dictionaries
    records = df.to_dict('records')

    # Convert timestamps to ISO format
    for record in records:
        if 'timestamp' in record and record['timestamp']:
            record['timestamp'] = record['timestamp'].isoformat()

    return jsonify({
        'status': 'success',
        'data': {
            'date': date.strftime('%Y-%m-%d'),
            'record_count': len(records),
            'records': records
        }
    })


@api_bp.route('/history/range', methods=['GET'])
@requires_auth
def get_history_range():
    """
    GET /api/v1/history/range?start=YYYY-MM-DD&end=YYYY-MM-DD

    Returns historical data for a date range.

    Query Parameters:
        start: Start date in YYYY-MM-DD format (required)
        end: End date in YYYY-MM-DD format (required)

    Returns:
        JSON response with historical data for the date range
    """
    if data_logger is None:
        return jsonify({'error': 'Data logger not initialized'}), 500

    # Get date range from query parameters
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    if not start_str or not end_str:
        return jsonify({
            'error': 'Both start and end dates are required. Use YYYY-MM-DD format'
        }), 400

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }), 400

    if start_date > end_date:
        return jsonify({
            'error': 'Start date must be before or equal to end date'
        }), 400

    # Get data for the date range
    df = data_logger.get_date_range_data(start_date, end_date)

    if df is None or df.empty:
        return jsonify({
            'status': 'success',
            'data': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'records': []
            }
        })

    # Convert DataFrame to list of dictionaries
    records = df.to_dict('records')

    # Convert timestamps to ISO format
    for record in records:
        if 'timestamp' in record and record['timestamp']:
            record['timestamp'] = record['timestamp'].isoformat()

    return jsonify({
        'status': 'success',
        'data': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'record_count': len(records),
            'records': records
        }
    })


@api_bp.route('/statistics', methods=['GET'])
@requires_auth
def get_statistics():
    """
    GET /api/v1/statistics?day=YYYY-MM-DD

    Returns statistical summary for a given day.

    Query Parameters:
        day: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        JSON response with statistics (min, max, mean, std) for the day
    """
    if data_logger is None:
        return jsonify({'error': 'Data logger not initialized'}), 500

    # Get date from query parameter or use today
    day_str = request.args.get('day')

    if day_str:
        try:
            date = datetime.strptime(day_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
    else:
        date = datetime.now()

    # Get statistics for the specified date
    stats = data_logger.get_statistics(date)

    if stats is None:
        return jsonify({
            'error': 'No data available for the specified date'
        }), 404

    return jsonify({
        'status': 'success',
        'data': stats
    })


@api_bp.route('/camera/latest', methods=['GET'])
@requires_auth
def get_latest_camera_image():
    """
    GET /api/v1/camera/latest

    Returns the latest camera image.

    Returns:
        Image file (JPEG)
    """
    from flask import current_app

    image_dir = Path(current_app.config.get('IMAGE_DIRECTORY', 'data/images'))

    if not image_dir.exists():
        return jsonify({
            'error': 'Image directory not found'
        }), 404

    # Find the most recent image file
    image_files = sorted(image_dir.glob('greenhouse_*.jpg'), reverse=True)

    if not image_files:
        return jsonify({
            'error': 'No images available'
        }), 404

    latest_image = image_files[0]

    return send_file(
        latest_image,
        mimetype='image/jpeg',
        as_attachment=False
    )


@api_bp.route('/camera/list', methods=['GET'])
@requires_auth
def list_camera_images():
    """
    GET /api/v1/camera/list?day=YYYY-MM-DD

    Returns a list of available camera images for a given day.

    Query Parameters:
        day: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        JSON response with list of image filenames and metadata
    """
    from flask import current_app

    # Get date from query parameter or use today
    day_str = request.args.get('day')

    if day_str:
        try:
            date = datetime.strptime(day_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
    else:
        date = datetime.now()

    image_dir = Path(current_app.config.get('IMAGE_DIRECTORY', 'data/images'))

    if not image_dir.exists():
        return jsonify({
            'error': 'Image directory not found'
        }), 404

    # Find images for the specified date
    date_str = date.strftime('%Y%m%d')
    pattern = f'greenhouse_{date_str}_*.jpg'
    image_files = sorted(image_dir.glob(pattern))

    images = []
    for img_file in image_files:
        images.append({
            'filename': img_file.name,
            'url': f'/api/v1/camera/image/{img_file.name}',
            'timestamp': img_file.stat().st_mtime,
            'size_bytes': img_file.stat().st_size
        })

    return jsonify({
        'status': 'success',
        'data': {
            'date': date.strftime('%Y-%m-%d'),
            'image_count': len(images),
            'images': images
        }
    })


@api_bp.route('/camera/image/<filename>', methods=['GET'])
@requires_auth
def get_camera_image(filename):
    """
    GET /api/v1/camera/image/<filename>

    Returns a specific camera image by filename.

    Args:
        filename: Image filename

    Returns:
        Image file (JPEG)
    """
    from flask import current_app

    image_dir = Path(current_app.config.get('IMAGE_DIRECTORY', 'data/images'))
    image_path = image_dir / filename

    # Security: Ensure the path is within the image directory
    if not image_path.resolve().is_relative_to(image_dir.resolve()):
        return jsonify({
            'error': 'Invalid filename'
        }), 400

    if not image_path.exists():
        return jsonify({
            'error': 'Image not found'
        }), 404

    return send_file(
        image_path,
        mimetype='image/jpeg',
        as_attachment=False
    )
