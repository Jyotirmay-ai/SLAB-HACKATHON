import subprocess
import sys
import os

os.chdir('D:\\software Projects\\SLAB hackathon\\qa_agent\\demo_site')
proc = subprocess.Popen([
    sys.executable, 'app.py'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'Flask PID: {proc.pid}')
import time
time.sleep(3)
print('Flask should be running now')