# Overview

This file is meant to highlight software capability and requirements of this repository. Documenting this will help ensure that the structure of the project is always guaranteed.

## Code Architecture

- `docs`
- `src`
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
- Virtual environment is built with uv
    - Support building on both windows machine (for testing/debugging)
    - Support building on linux machine (deployed Raspberry Pi)


