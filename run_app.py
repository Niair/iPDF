"""
Main application runner
"""
import subprocess
import sys
import os
from pathlib import Path

def run_app():
    """Run the Streamlit application"""
    try:
        # Get the path to the app
        app_path = Path(__file__).parent / "src" / "ui" / "app.py"
        
        # Check if the app file exists
        if not app_path.exists():
            print(f"Error: App file not found at {app_path}")
            return False
        
        print("Starting iPDF application...")
        print(f"App path: {app_path}")
        
        # Run streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
        print(f"Running: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(cmd, check=True)
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_app()
    if not success:
        sys.exit(1)
