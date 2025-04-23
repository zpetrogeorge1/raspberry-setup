import os
import subprocess
import sys
import shutil

VENV_DIR = os.path.expanduser("~/my_env")
PYTHON_VERSION = "3.9.10"
PYTHON_BUILD_DIR = os.path.expanduser("~/python-build")
PYTHON_BIN = os.path.join(PYTHON_BUILD_DIR, "bin", "python3.9")

def run_command(command, description):
    """Run a shell command and print output."""
    print(f"\n[+] {description}...")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()  # Wait for completion and capture output
    print(stdout)
    if process.returncode == 0:
        print(f"Success: {description}")
    else:
        print(f"Error: {description}\n{stderr}")
        return False
    return True

def check_disk_space(min_space_gb=3):
    """Check if there's enough disk space (in GB)."""
    total, used, free = shutil.disk_usage("/")
    if free // (2**30) < min_space_gb:
        print(f"Error: Insufficient disk space. Need {min_space_gb}GB, have {free // (2**30)}GB.")
        exit(1)
    print(f"Disk space check: {free // (2**30)}GB available, proceeding...")

def check_local_python():
    """Check if the locally built Python 3.9.10 exists."""
    return os.path.exists(PYTHON_BIN)

def build_python():
    """Download and compile Python 3.9.10 locally."""
    if check_local_python():
        print("Python 3.9.10 is already built.")
        return True
    
    print("Building Python 3.9.10 locally (this may take some time)...")

    # Install build dependencies for Python
    if not run_command(
        "sudo apt update && sudo apt install -y build-essential zlib1g-dev libncurses5-dev "
        "libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl libbz2-dev",
        "Installing Python build dependencies"
    ):
        return False
    
    # Build Python with limited jobs (-j2) for Raspberry Pi
    build_cmd = (
        f"mkdir -p {PYTHON_BUILD_DIR} && cd {PYTHON_BUILD_DIR} && "
        "wget https://www.python.org/ftp/python/3.9.10/Python-3.9.10.tgz && "
        "tar -xf Python-3.9.10.tgz && cd Python-3.9.10 && "
        f"./configure --prefix={PYTHON_BUILD_DIR} --enable-optimizations && "
        "make -j2 && make install"
    )
    if not run_command(build_cmd, "Downloading and compiling Python 3.9.10"):
        return False
    return check_local_python()

def create_virtual_environment():
    """Create a virtual environment using the locally built Python 3.9.10."""
    if not check_local_python():
        print("Local Python 3.9.10 not found. Building now...")
        if not build_python():
            print("Build failed. Cannot proceed with virtual environment creation")
            exit(1)
    
    if not os.path.exists(VENV_DIR):
        run_command(f"{PYTHON_BIN} -m venv {VENV_DIR}", f"Creating virtual environment with Python {PYTHON_VERSION}")
    else:
        print("Virtual environment already exists")

def activate_and_setup():
    """Activate virtual environment and install essential packages."""
    # Install system dependencies for libraries
    run_command(
        "sudo apt install -y libatlas-base-dev gfortran libgl1-mesa-glx libglib2.0-0",
        "Installing system dependencies for numpy, opencv, and mediapipe"
    )
    
    # Upgrade pip
    run_command(f"{VENV_DIR}/bin/python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install required Python libraries
    libraries = [
        "numpy",
        "opencv-python",
        "mediapipe",
        "pandas",
        "openpyxl",
        "scikit-learn"
    ]
    run_command(
        f"{VENV_DIR}/bin/python -m pip install {' '.join(libraries)}",
        f"Installing Python libraries: {', '.join(libraries)}"
    )

def main():
    print("Starting Virtual Environment Setup with Python 3.9.10")
    
    # Check disk space before proceeding
    check_disk_space(min_space_gb=3)

    create_virtual_environment()
    activate_and_setup()

    print("\nSetup complete! To activate the virtual environment, run:")
    print(f"    source {VENV_DIR}/bin/activate")
    print(f"    python --version  # Should print {PYTHON_VERSION}")
    print("All required libraries (mediapipe, opencv-python, numpy, pandas, openpyxl, scikit-learn) are installed.")
    print("Standard libraries (json, datetime, os, time, subprocess, sys, shutil) are available by default.")

if __name__ == "__main__":
    main()
