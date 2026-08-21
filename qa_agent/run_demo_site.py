import subprocess
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), "demo_site"))
subprocess.run([sys.executable, "app.py"])