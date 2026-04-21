import sys
import os
from pathlib import Path
import shutil
import subprocess
import webbrowser

def script():
    project_root = Path(__file__).resolve().parent.parent
    venv_dir = project_root / "venv"
    env_file = venv_dir / ".env"
    
    # Ensure the venv directory exists so we can place .env inside it
    os.makedirs(venv_dir, exist_ok=True)
    
    if not env_file.exists():
        api_key = input("Insert your riot API key: ")
        with open(env_file, "w") as f:
            f.write(f"RIOT_API_KEY={api_key}\n")
        print(f"Successfully saved API key to {env_file}")
    else:
        print(f"Existing .env file found at {env_file}.")
        
    src_dir = project_root / "src"
    # Use sys.executable to securely call global uvicorn module
    subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app', '--reload'], cwd=src_dir)
    print("Server is ready and working! :)")

    front_dir = project_root / "src" / "FRONTEND"
    npm_path = shutil.which("npm")
    if npm_path:
        subprocess.Popen([npm_path, 'run', 'dev'], cwd=front_dir)

if __name__ == "__main__":
    script()
    webbrowser.open("http://localhost:5173/")