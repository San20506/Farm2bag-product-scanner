import subprocess
import sys
import time
import os
import signal

def get_python_path():
    """Ensure we use the local virtual environment's python if it exists."""
    venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

def main():
    print("🚀 Starting PriceTrackerPro Project...\n")
    
    # Try starting the MongoDB container just in case it stopped
    print("📦 Checking MongoDB docker container...")
    subprocess.run(["docker", "start", "mongo"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    python_exe = get_python_path()
    
    print("\n⚙️  Starting backend API server (Port 8001)...")
    backend_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=os.path.join(os.getcwd(), "backend")
    )
    
    time.sleep(1) # Give backend a second to print its startup logs
    
    print("\n🎨 Starting frontend UI server (Port 3001)...")
    frontend_process = subprocess.Popen(
        [python_exe, "-m", "http.server", "3001"],
        cwd=os.path.join(os.getcwd(), "website")
    )
    
    print("\n✅ All services started! Press Ctrl+C to stop.")
    print("🔗 Frontend Dashboard: http://localhost:3001")
    print("🔗 Backend API:       http://localhost:8001/docs\n")
    
    # Handle graceful shutdown
    def cleanup(signum, frame):
        print("\n\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("👋 Goodbye!")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    main()
