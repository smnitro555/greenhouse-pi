# Overview

This file is meant to highlight software capability and requirements of this repository. Documenting this will help ensure that the structure of the project is always guaranteed.

## Code Architecture

- `docs`
    - Location for sphinx documentation that highlights the following topics:
        - Changelog
        - GPIO Pins for Raspi Setup
            - Explain which pins for Temperature and Humidity sensor
            - 
            - (Vector graphic images)
        - Software architecture diagram
        - Sphinx Auto-Doc of Python code base
- `src`
    - `raspi`
        - `greenhouse_driver_start.sh`
            - Script that Raspberry Pi will point to on boot up
                - Ensures packages are updated
                - Pulls the latest version from Github
                - Starts the `greenhouse_manager.py`
                - Starts hosting the webserver
    - `greenhouse_manager`
        - `greenhouse_manager.py`
            - Main script that will run continuously
            - Settings should be read from a pydantic JSON file
            - Logic should continously do the following
                - Continously
                    - Check if settings file has been updated
                    - Monitor Temperature and Humidity
                    - Adjust heater and vent fan accordingly
                    - Based on time schedule turn on/off grow lights
                    - Based on time schedule turn on/off
                    - Based on time schedule take images of greenhouse
                    - Write state information (date, 24hr time, greenhouse temp, greenhouse humidity, greenhouse pressure, heater state, vent state, grow lights, stand fan) to log files
                        - One log file per day ideally
                        - Pandas DataFrame for each day
                        - (binary format to save space)
                - On Interupt from GPIO Button
                    - Turn on/off the device
                    - Illuminate the button
    - `webserver`
        - Utilize flask to generate the website (Should be dynamic, allowing to refresh on new data that is being written)
        - Code related to hosting a Plotly dashboard of time vs. remaining parameters (X axis on all plots is datetime (default zoom is for the current day, but allow for week, month type views))
        - Code related to hosting a image slideshow with a time slider to see time-lapse of greenhouse state

- `test`

## Development Operations

- Working documentation
- Python to build the following install targets for:
    - `build` for building the virtual environment and docs
        - `build-env` for building the virtual enviroment
        - `build-doc` for building the docs
    - `run` for launching the Python greenhouse client and web server
        - `run-greenhouse` to run just the Python greenhouse client
        - `run-webserver` to host the webserver 
- Pytest framework (also utilizing doctest)
    - Allow mock testing of GPIO capability
    - Use doctest to check public methods
- Virtual environment is built with uv
    - Support building on both windows machine (for testing/debugging)
    - Support building on linux machine (deployed Raspberry Pi)


