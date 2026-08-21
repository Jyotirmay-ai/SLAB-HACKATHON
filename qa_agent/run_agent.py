import asyncio
import sys
import os

import subprocess

# Auto-switch to project .venv python if available
venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe"))
if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower():
    sys.exit(subprocess.call([venv_python] + sys.argv))
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator.orchestrator import Orchestrator


async def main():
    orchestrator = Orchestrator(headless=False, approval_mode="cli")
    await orchestrator.run_flow()


if __name__ == "__main__":
    asyncio.run(main())