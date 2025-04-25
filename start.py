import subprocess
import sys
import os
import venv
from threading import Thread
import time
import site
import shutil

def ensure_venv():
    """Ensure we have a virtual environment and it's activated"""
    venv_dir = os.path.join(os.path.dirname(__file__), '.venv')
    
    # Create venv if it doesn't exist
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    
    # Get the path to the Python executable in the venv
    if sys.platform == 'win32':
        python_path = os.path.join(venv_dir, 'Scripts', 'python.exe')
        pip_path = os.path.join(venv_dir, 'Scripts', 'pip.exe')
        skuld_path = os.path.join(venv_dir, 'Scripts', 'skuld.exe')
    else:
        python_path = os.path.join(venv_dir, 'bin', 'python')
        pip_path = os.path.join(venv_dir, 'bin', 'pip')
        skuld_path = os.path.join(venv_dir, 'bin', 'skuld')
    
    if not os.path.exists(python_path):
        raise RuntimeError("Failed to create virtual environment")
    
    return python_path, pip_path, skuld_path

def find_npm():
    """Find npm executable"""
    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    npm_path = shutil.which(npm_cmd)
    
    if not npm_path:
        # Try common Node.js installation paths on Windows
        if sys.platform == 'win32':
            common_paths = [
                os.path.join(os.environ.get('ProgramFiles', ''), 'nodejs', 'npm.cmd'),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'nodejs', 'npm.cmd'),
                os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm.cmd')
            ]
            for path in common_paths:
                if os.path.exists(path):
                    npm_path = path
                    break
    
    if not npm_path:
        raise RuntimeError("npm not found. Please install Node.js and npm.")
    
    return npm_path

def install_package(python_path, pip_path):
    """Install the package if not already installed"""
    try:
        # Try importing the package to check if it's installed
        subprocess.run([python_path, '-c', 'import skuld'], check=True)
    except subprocess.CalledProcessError:
        print("Installing Skuld package...")
        subprocess.run([pip_path, 'install', '-e', '.'], check=True)

def run_frontend(npm_path):
    """Run the frontend development server"""
    frontend_dir = os.path.join('skuld', 'frontend')
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("Installing frontend dependencies...")
        subprocess.run([npm_path, 'install'], cwd=frontend_dir, check=True)
    
    print("Starting React development server...")
    subprocess.run([npm_path, 'start'], cwd=frontend_dir)

def run_backend(skuld_path):
    """Run the backend server"""
    print("Starting Skuld server...")
    subprocess.run([skuld_path, 'run'])

def main():
    try:
        # Find npm
        npm_path = find_npm()
        print(f"Found npm at: {npm_path}")
        
        # Ensure we have a virtual environment and get its Python path
        python_path, pip_path, skuld_path = ensure_venv()
        
        # Install the package if needed
        install_package(python_path, pip_path)
        
        # Start the backend in a separate thread
        backend_thread = Thread(target=run_backend, args=(skuld_path,))
        backend_thread.daemon = True
        backend_thread.start()
        
        # Give the backend time to start
        time.sleep(2)
        
        # Start the frontend in the main thread
        run_frontend(npm_path)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting services: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 