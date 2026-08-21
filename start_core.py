#!/usr/bin/env python
"""
Self-Healing QA Agent - Core System Launcher
Starts the Flask demo site and QA Agent.
Dashboard to be started separately.

Press Ctrl+C to stop the agent (Flask will keep running).
"""

import subprocess
import sys
import os
import time
import signal

# paths
PROJECT_ROOT = r"D:\software Projects\SLAB hackathon"
QA_AGENT_DIR = os.path.join(PROJECT_ROOT, "qa_agent")
DEMO_SITE_DIR = os.path.join(QA_AGENT_DIR, "demo_site")

processes = []

def start_flask():
    """Start the Flask demo site"""
    print("[INFO] Starting Flask demo site...")
    cmd = [
        os.path.join(".venv", "Scripts", "python.exe"),
        os.path.join(DEMO_SITE_DIR, "app.py")
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=DEMO_SITE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(("Flask", proc))
    print(f"   [OK] Flask started on http://127.0.0.1:5000 (PID: {proc.pid})")
    time.sleep(3)

def start_agent():
    """Start the QA Agent"""
    print("[AGENT] Starting QA Agent...")
    cmd = [
        os.path.join(".venv", "Scripts", "python.exe"),
        "run_agent.py"
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=QA_AGENT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(("QA Agent", proc))
    print(f"   [RUNNING] QA Agent running (PID: {proc.pid})")
    print("   [INFO] The agent will:")
    print("      - Log in to the demo site")
    print("      - Run the flow: login -> search -> cart -> checkout")
    print("      - [PAUSE] Pause at approval gate (waiting for 'y' input)")
    print("      - [RECOVER] Auto-recover from selector changes if site is broken")
    print()

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\n[STOP] Stopping QA Agent...")
    for name, proc in processes:
        if name == "QA Agent":
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("   [OK] QA Agent stopped")
    print("   [INFO] Flask demo site still running...")
    print("   [DASHBOARD] Start dashboard separately: streamlit run qa_agent/dashboard/app.py")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("SELF-HEALING QA AGENT - CORE SYSTEM")
    print("=" * 60)
    print()
    print("Components starting:")
    print("  1. Flask demo site...   ")
    start_flask()
    print("  2. QA Agent...          ")
    start_agent()
    print()
    print("=" * 60)
    print("System active. Press Ctrl+C to stop the QA Agent.")
    print("   Flask will keep running in the background.")
    print("   Start dashboard separately:")
    print("   streamlit run qa_agent/dashboard/app.py")
    print()
    
    # Keep running while agent process is alive
    try:
        while True:
            if len(processes) > 1 and processes[1][1].poll() is not None:  # QA Agent process ended
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()