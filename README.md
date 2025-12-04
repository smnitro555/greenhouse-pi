# Greenhouse-Pi

Repository to manage code for Raspberry Pi controlled greenhouse. This repository will contain both the python code and the html template to host on the Raspberry Pi.

## Setup

This project uses `uv` for Python package management. To create a virtual environment and install the dependencies, run the following commands:

```bash
uv venv
uv pip install -e .
```

## Code Structure

This code base is designed to be run on a Raspberry Pi as a local server that monitors greenhouse temperature and humidity to regulate a greenhouse. The functionality of this system is to:

- Provide a dashboard via a web-server with historical temperature/humidity data both in the greenhouse and outisde temperature (web)
- Take time-lapse photographs of the current state in the greenhouse. Support for N number of cameras.
- Raspberry Pi will be connected to illuminated switches, which should control radio controlled outlets. These outlets control:
    - Heater - Increase the temperature of the greenhouse
    - Vent Fan - Decrease the temperature of the greenhouse (Opens the vent to blow air from inside to out)
    - Stand Fan - Fan to circulate air in greenhouse. Important for strengthening plants
    - Grow Lights - Used for seedline trays to ensure that additional light is present

Additional code base specific documentation can be found in the `repository_structure_requirements.md` file in this repository.