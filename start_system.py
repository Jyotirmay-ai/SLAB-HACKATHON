#!/usr/bin/env python
"""
Self-Healing QA Agent - System Launcher
Starts all components: Flask demo site, QA Agent, and Dashboard.
Press Ctrl+C to stop all components.
"""

import subprocess
import sys
import os
import time
import signal
import threading

# paths
PROJECT_ROOT = r"D:\software Projects\SLAB hackathon"
QA_AGENT_DIR = os.path.join(PROJECT_ROOT, "qa_agent")
DEMO_SITE_DIR = os.path.join(QA_AGENT_DIR, "demo_site")
DASHBOARD_DIR = os.path.join(QA_AGENT_DIR, "dashboard")

processes = []

def start_flask():
    """Start the Flask demo site"""
    print("🟢 Starting Flask demo site...")
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
    print(f"   PID: {proc.pid}")
    time.sleep(3)  # Wait for Flask to start
    print("   ✅ Flask is running on http://127.0.0.1:5000\n")

def start_agent():
    """Start the QA agent"""
    print("🤖 Starting QA Agent...")
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
    print(f"   PID: {proc.pid}")
    print("   The agent will run and pause at the approval gate")
    print("   💡 Tip: Type 'y' at the approval prompt to continue\n")

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("📊 Starting Dashboard...")
    cmd = [
        os.path.join(".venv", "Scripts", "python.exe"),
        "-m", "streamlit", "run", "dashboard/app.py",
        "--server.port", "8501",
        "--server.headless", "false"
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=QA_AGENT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(("Dashboard", proc))
    print(f"   PID: {proc.pid}")
    print("   📈 Dashboard will open at http://localhost:8501\n")

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully stop all processes"""
    print("\n🛑 Stopping all components...")
    for name, proc in processes:
        print(f"   Stopping {name} (PID: {proc.pid})...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("   ✅ All components stopped")
    sys.exit(0)

def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("SELF-HEALING QA AGENT - SYSTEM LAUNCHER")
    print("=" * 60)
    print()
    print("This will start all three components:")
    print("  1. Flask demo site (http://127.0.0.1:5000)")
    print("  2. QA Agent (runs the QA flow)")
    print("  3. Dashboard (http://localhost:8501)")
    print()
    print("Press Ctrl+C at any time to stop all components")
    print()
    
    # Start all components
    start_flask()
    start_agent()
    start_dashboard()
    
    print("=" * 60)
    print("All components are running...")
    print("=" * 60)
    print()
    print("To stop all components, press Ctrl+C")
    print()
    
    # Keep the main thread alive while processes run
    try:
        while True:
            # Check if all processes are still alive
            all_running = True
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"   ⚠️ {name} has exited (code: {proc.returncode})")
                    all_running = False
            
            if not all_running:
                break
            
            time.sleep(2)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()