import os
import subprocess

VENV_DIR = os.path.expanduser("~/my_env")
PYTHON_VERSION = "3.9.10"
PYTHON_BUILD_DIR = os.path.expanduser("~/python-build")
PYTHON_BIN = os.path.join(PYTHON_BUILD_DIR, "python3.9")

def run_command(command, description):
    """Run a shell command and print output."""
    print(f"\n[+] {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Success: {description}")
    else:
        print(f"Error: {description}\n{result.stderr}")

def check_local_python():
    """Check if the locally built Python 3.9.10 exists."""
    return os.path.exists(PYTHON_BIN)

def build_python():
    """Download and compile Python 3.9.10 locally."""
    if check_local_python():
        print("Python 3.9.10 is already built.")
        return 
    
    print("Building Python 3.9.10 locally (this may take some time)...")

    run_command(f"mkdir -p {PYTHON_BUILD_DIR} && CD {PYTHON_BUILD_DIR} && "
                "wget https://www.python.org/ftp/python/3.9.10/Python-3.9.10.tgz && "
                "tar -xf Python-3.9.10.tgz && cd Python-3.9.10 && "
                "./configure --prefix=$HOME/python-build --enable-optimizations && "
                "make -j$(nproc) && make install",
                "Downloading and compiling Python 3.9.10")
    

def create_virtual_environment():
    """Create a virtual environment using the locally built python 3.9.10"""
    if not check_local_python():
        print("Local Python 3.9.10 not found. Building now...")
        build_python()
    
    if not os.path.exists(VENV_DIR):
        run_command(f"{PYTHON_BIN} -m venv {VENV_DIR}", f"Creating virtual environment with Python {PYTHON_VERSION}")
    else:
        print("Virtual environment already exists")

def activate_and_setup():
    """Activate virtual environment and install essential packages."""
    run_command(f"{VENV_DIR}/bin/python -m pip install --upgrade pip", "Upgrading pip")
    run_command(f"{VENV_DIR}/bin/python -m pip install numpy matplotlib", "Installing essential packages")

def main():
    print("Starting Virtual Environment Setup with Python 3.9.10")

    create_virtual_environment()
    activate_and_setup()

    print("\nSetup complete! to activate the virtual environment, run:")
    print(f"    source {VENV_DIR}/bin/activate")
    print(f"    python --version # Should print {PYTHON_VERSION}")

if __name__ == "__main__":
    main()
