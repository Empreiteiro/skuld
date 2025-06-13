import os
import sys
import subprocess
from threading import Thread
import time
import webbrowser

def ensure_venv():
    """Ensure virtual environment exists and return paths"""
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
    
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
    
    if sys.platform == 'win32':
        python_path = os.path.join(venv_dir, 'Scripts', 'python.exe')
        pip_path = os.path.join(venv_dir, 'Scripts', 'pip.exe')
        buffer_path = os.path.join(venv_dir, 'Scripts', 'buffer.exe')
    else:
        python_path = os.path.join(venv_dir, 'bin', 'python')
        pip_path = os.path.join(venv_dir, 'bin', 'pip')
        buffer_path = os.path.join(venv_dir, 'bin', 'buffer')
    
    return python_path, pip_path, buffer_path

def install_package(python_path, pip_path):
    """Install the package in development mode"""
    try:
        subprocess.run([python_path, '-c', 'import buffer'], check=True)
    except subprocess.CalledProcessError:
        print("Installing Buffer package...")
        subprocess.run([pip_path, 'install', '-e', '.'], check=True)

def run_frontend():
    """Run the frontend development server"""
    frontend_dir = os.path.join('buffer', 'frontend')
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory not found: {frontend_dir}")
        return
    
    os.chdir(frontend_dir)
    subprocess.run(['npm', 'install'], check=True)
    subprocess.run(['npm', 'start'])

def run_backend(buffer_path):
    """Run the backend server"""
    try:
        print("Starting Buffer server...")
        subprocess.run([buffer_path, 'run'])
    except KeyboardInterrupt:
        print("\nStopping Buffer server...")

def main():
    """Main function to start both frontend and backend"""
    try:
        # Ensure virtual environment and install package
        python_path, pip_path, buffer_path = ensure_venv()
        install_package(python_path, pip_path)
        
        # Start backend in a separate thread
        backend_thread = Thread(target=run_backend, args=(buffer_path,))
        backend_thread.daemon = True
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(2)
        
        # Start frontend
        run_frontend()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 