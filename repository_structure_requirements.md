# Overview

This file is meant to highlight software capability and requirements of this repository. Documenting this will help ensure that the structure of the project is always guaranteed.

The goal of this project is to generate a greenhouse management software that can provide the status of the greenhouse through a web-server. For hardware, a raspberry pi will be used that
has temperature and humidity sensor, as well as additional buttons that can control the state of greenhouse appliances (fans, vents, etc.).

## Code Architecture

- `docs/`
    - Location for sphinx documentation that highlights the following topics:
        - Changelog
        - GPIO Pins for Raspi Setup
            - Explain which pins for Temperature and Humidity sensor
            - (Vector graphic images)
        - Software architecture diagram
        - Sphinx Auto-Doc of Python code base

- `src/`
    - `__init__.py`
    - `raspi/`
        - `__init__.py`
        - `greenhouse_driver_start.sh`
            - Script that Raspberry Pi will point to on boot up
                - Ensures packages are updated
                - Pulls the latest version from Github
                - Sets up the virtual environment (`build-env`)
                - Configures and enables systemd services for the manager and webserver
                - Starts the `greenhouse_manager.py` via a systemd service (`run-greenhouse`)
                - Starts hosting the webserver via a systemd service (`run-webserver`)
                - Logic to ensure that if `run-greenhouse` or `run-webserver` crash, they will be restarted
                    - Sending an email to users based on a configuration file if crashes are frequent (stored in `config/private-data/`)
    - `greenhouse_manager/`
        - `__init__.py`
        - `greenhouse_manager.py`
            - Main script that will run continuously
            - Settings should be loaded from a JSON configuration file (`config/greenhouse_manager_settings.json`)
            - Settings are validated using the Pydantic model defined in `greenhouse_manager_settings.py`
            - Logic should continously do the following:
                - Continuously:
                    - Check if settings file has been updated
                    - Monitor Temperature and Humidity
                    - Adjust heater and vent fan accordingly
                    - Based on time schedule turn on/off grow lights
                    - Based on time schedule turn on/off stand fan
                    - Based on time schedule take images of greenhouse
                    - Write state information (date, 24hr time, greenhouse temp, greenhouse humidity, greenhouse pressure, heater state, vent state, grow lights, stand fan) to log files
                - On Interrupt from GPIO Button:
                    - Toggle the state of the associated device
                    - Illuminate the button
        - `greenhouse_manager_settings.py`
            - Pydantic class that defines the settings schema for the greenhouse manager
            - Provides validation and type checking for configuration loaded from JSON
        - `greenhouse_hardware_collection.py`
            - Module that contains classes for the different pieces of hardware (`BME280Sensor`, `RFOutlet`, and `Button`)
            - Support for mock behaviours, to allow for testing without running on the actual hardware
        - `greenhouse_data_logger.py`
            - Class for managing the log data
            - One log file per day ideally
            - Pandas DataFrame for each day
            - Accepts the data from the `greenhouse_manager.py` to organize into the log files
            - Use a space-efficient binary format like Apache Parquet or Feather for storing dataframes
            - Writes log files to `data/logs/`

    - `webserver/`
        - `__init__.py`
        - `app.py`
            - Main Flask application entry point
            - This code should be designed to be run seperately from the `greenhouse_manager.py` process on the raspberry pi
            - Utilize Flask to generate the website (Should be dynamic, allowing to refresh on new data that is being written)
            - Add basic authentication to protect the web interface and API endpoints
        - `api/`
            - `__init__.py`
            - Flask REST API endpoints:
                - GET /api/v1/status: Returns the latest sensor readings and device states
                - GET /api/v1/history?day=YYYY-MM-DD: Returns the historical data for a given day
                - GET /api/v1/camera/latest: Returns the latest image
        - `templates/`
            - HTML templates for Flask web interface
            - Plotly dashboard of time vs. remaining parameters (X axis on all plots is datetime (default zoom is for the current day, but allow for week, month type views))
            - Image slideshow with a time slider to see time-lapse of greenhouse state

- `tests/`
    - `__init__.py`
    - Folder for all test files (using pytest framework)
    - `test_greenhouse_manager.py`
    - `test_webserver.py`
    - `test_hardware_collection.py`

- `config/`
    - `greenhouse_manager_settings.json`
        - Example/template configuration file for greenhouse manager settings
    - `rf_keys.yaml`
        - Configuration for RF outlet keys
    - `private-data/`
        - `.gitkeep`
        - Directory for sensitive configuration (email credentials, etc.)
        - This directory should be added to `.gitignore`

- `data/`
    - `logs/`
        - `.gitkeep`
        - Storage for daily log files (Parquet/Feather format)
        - This directory should be added to `.gitignore`
    - `images/`
        - `.gitkeep`
        - Storage for greenhouse images captured on schedule
        - This directory should be added to `.gitignore`

- `systemd/`
    - `greenhouse-manager.service`
        - Template systemd service file for greenhouse manager
    - `greenhouse-webserver.service`
        - Template systemd service file for webserver

- `.github/`
    - `workflows/`
        - `ci.yml`
            - GitHub Actions workflow for continuous integration
            - Runs tests and linter on push/pull_request to main branch

## Development Operations

### Build System
- `build.py` - Python-based build script with the following targets:
    - `build` - Build the virtual environment and docs (runs both build-env and build-doc)
        - `build-env` - Build the virtual environment using uv
        - `build-doc` - Build Sphinx documentation
    - `run` - Launch the Python greenhouse client and web server
        - `run-greenhouse` - Run just the Python greenhouse client
        - `run-webserver` - Host the webserver

### Testing Framework
- Pytest framework (also utilizing doctest)
    - Allow mock testing of GPIO capability
    - Use doctest to check public methods
    - Tests located in `tests/` directory
    - Mock hardware implementations in `greenhouse_hardware_collection.py` for testing on non-Raspberry Pi systems

### Continuous Integration
- GitHub Actions CI using `.github/workflows/ci.yml`
    - On push/pull_request to `main`, run:
        - Tests (pytest)
        - Linter (Ruff)
        - Type checker (mypy)
        - Code formatter check (Black)

### Virtual Environment
- Virtual environment is built with uv
    - Support building on both Windows machine (for testing/debugging)
    - Support building on Linux machine (deployed Raspberry Pi)
    - Python 3.11+ required

### Project Configuration
- `pyproject.toml` includes:
    - Project metadata and dependencies
    - Optional dev dependencies (pytest, ruff, mypy, black)
    - Entry point scripts for greenhouse-manager and greenhouse-webserver
    - Tool configurations (pytest, ruff, mypy, black)

### Additional Files
- `.gitignore` - Excludes:
    - Virtual environment (`.venv/`)
    - Python cache files (`__pycache__/`, `*.pyc`)
    - Build artifacts (`*.egg-info/`, `docs/build/`)
    - Data directories (`data/logs/`, `data/images/`)
    - Private configuration (`config/private-data/`)
    - Tool caches (`.mypy_cache/`, `.pytest_cache/`)
    - Binary data files (`*.parquet`, `*.feather`)
