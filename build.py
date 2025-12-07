import subprocess
import sys
import os
import shutil

VENV_DIR = ".venv"


def run_command(command, cwd=None):
    """A helper function to run a command in a subprocess."""
    print(f"Executing: {' '.join(command)}")
    try:
        # On Windows, we need to use shell=True to ensure commands from the
        # virtual environment's Scripts directory (like 'sphinx-build' or 'uv')
        # are found if the venv is not globally activated.
        # For other platforms, it's safer to avoid shell=True.
        # The command list is joined into a string for shell execution.
        if sys.platform == "win32":
            command = " ".join(command)

        is_windows = sys.platform == "win32"
        subprocess.run(command, check=True, cwd=cwd, shell=is_windows)
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is it installed and in your PATH?")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def build_env():
    """Creates the virtual environment and installs dependencies."""
    # 1. Delete the existing venv if it exists
    if os.path.exists(VENV_DIR):
        print(f"--- Deleting existing virtual environment: {VENV_DIR} ---")
        shutil.rmtree(VENV_DIR)

    print("--- Creating Virtual Environment using python -m venv ---")
    run_command([sys.executable, "-m", "venv", VENV_DIR])

    # Determine the path to the python executable in the venv
    python_executable = os.path.join(VENV_DIR, "Scripts" if sys.platform == "win32" else "bin", "python")

    print("\n--- Installing uv into the virtual environment ---")
    run_command([python_executable, "-m", "pip", "install", "uv"])

    # Determine the path to the uv executable in the venv
    uv_executable = os.path.join(VENV_DIR, "Scripts" if sys.platform == "win32" else "bin", "uv")

    print("\n--- Installing dependencies using uv sync ---")
    # uv sync will install all dependencies from pyproject.toml
    run_command([uv_executable, "sync"])
    print("\nVirtual environment ready.")


def build_doc():
    """Builds the Sphinx documentation."""
    print("\n--- Building Documentation ---")

    # 2. Ensure sphinx-build is run from the virtual environment
    python_exe_name = "python.exe" if sys.platform == "win32" else "python"
    python_executable = os.path.join(VENV_DIR, "Scripts" if sys.platform == "win32" else "bin", python_exe_name)
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found in venv at {python_executable}")
        print("Please run 'python build.py build-env' first.")
        sys.exit(1)

    source_dir = os.path.join("docs", "source")
    build_dir = os.path.join("docs", "build")
    run_command([python_executable, "-m", "sphinx", "-M", "html", source_dir, build_dir])
    print(f"\nDocumentation built in {os.path.join(build_dir, 'html')}")


def build_all():
    """Runs all build steps."""
    build_env()
    build_doc()


def run_greenhouse():
    """Runs the greenhouse manager."""
    print("\n--- Starting Greenhouse Manager ---")
    python_executable = os.path.join(VENV_DIR, "Scripts" if sys.platform == "win32" else "bin", "python")

    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found in venv at {python_executable}")
        print("Please run 'python build.py build-env' first.")
        sys.exit(1)

    # Run the greenhouse manager
    run_command([python_executable, "-m", "greenhouse_manager.greenhouse_manager"])


def run_webserver():
    """Runs the Flask webserver."""
    print("\n--- Starting Webserver ---")
    python_executable = os.path.join(VENV_DIR, "Scripts" if sys.platform == "win32" else "bin", "python")

    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found in venv at {python_executable}")
        print("Please run 'python build.py build-env' first.")
        sys.exit(1)

    # Run the webserver (will be implemented later)
    webserver_path = os.path.join("src", "webserver", "app.py")
    if os.path.exists(webserver_path):
        run_command([python_executable, webserver_path])
    else:
        print(f"Error: Webserver not found at {webserver_path}")
        print("Webserver not yet implemented.")
        sys.exit(1)


def run_all():
    """Runs both the greenhouse manager and webserver (in separate processes would be ideal)."""
    print("\n--- Note: This will run greenhouse manager first ---")
    print("--- To run webserver separately, use 'python build.py run-webserver' in another terminal ---")
    run_greenhouse()


if __name__ == "__main__":
    # A simple command-line argument parser
    commands = {
        "build": build_all,
        "build-env": build_env,
        "build-doc": build_doc,
        "run": run_all,
        "run-greenhouse": run_greenhouse,
        "run-webserver": run_webserver,
    }

    # Default to 'build' if no arguments are provided
    command_to_run = sys.argv[1] if len(sys.argv) > 1 else "build"

    if command_to_run in commands:
        commands[command_to_run]()
    else:
        print(f"Unknown command: {command_to_run}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)