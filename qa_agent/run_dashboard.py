import subprocess
import sys
import os

# Auto-switch to project .venv python if available
venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe"))
if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower():
    sys.exit(subprocess.call([venv_python] + sys.argv))

os.chdir(os.path.join(os.path.dirname(__file__), "dashboard"))
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"])