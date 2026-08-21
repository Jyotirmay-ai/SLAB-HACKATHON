import subprocess
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), "dashboard"))
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"])