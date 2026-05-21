import sys
import os
from pathlib import Path
import shutil
import subprocess
import webbrowser
import time
import platform

def script():
    project_root = Path(__file__).resolve().parent.parent.parent
    env_file = project_root / ".env"
    
    # Ensure the venv directory exists so we can place .env inside it
    os.makedirs(env_file, exist_ok=True)
    
    if not env_file.exists():
        api_key = input("Insert your riot API key: ")
        with open(env_file, "w") as f:
            f.write(f"RIOT_API_KEY={api_key}\n")
        print(f"Successfully saved API key to {env_file}")
    else:
        print(f"Existing .env file found at {env_file}.")
        
    src_dir = project_root / "src"
    backend_dir = src_dir / "BACKEND"
    # if macOS, kill uvicorn instances
    if platform.system() == "darwin":
        subprocess.run(["pkill", "-f", "uvicorn"])
    time.sleep(0.5)
    # Use sys.executable to securely call global uvicorn module
    subprocess.Popen([sys.executable, '-m', 'uvicorn', 'BACKEND.main:app', '--reload'], cwd=src_dir)
    print("Server is ready and working! :)")

    front_dir = project_root / "src" / "FRONTEND"
    npm_path = shutil.which("npm")
    if npm_path:
        subprocess.Popen([npm_path, 'run', 'dev'], cwd=front_dir)

if __name__ == "__main__":
    script()
    time.sleep(0.5)
    webbrowser.open("http://localhost:5173/")