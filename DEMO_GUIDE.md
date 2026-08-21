# 🚀 Self-Healing QA Agent - Demo Guide

This guide provides the exact sequence of steps to demonstrate the self-healing capabilities of the QA Agent during the hackathon presentation.

## 🛠️ Setup & Environment

### 1. Start the Core System (Flask + Agent)
Open a terminal and run:
```cmd
cd "D:\software Projects\SLAB hackathon"
python start_core.py
```
*This starts the demo shop on `http://127.0.0.1:5000` and launches the QA Agent.*

### 2. Start the Dashboard (Separate Terminal)
Open a second terminal and run:
```cmd
cd "D:\software Projects\SLAB hackathon\qa_agent"
python -m streamlit run dashboard/app.py
```
*The dashboard will open at `http://localhost:8501`.*

---

## 🎬 The Demo Sequence

### Phase 1: The "Happy Path" (Everything Works)
**Goal:** Show that the agent can complete a full purchase flow without issues.

1. **Execution:** The agent starts automatically from `start_core.py`.
2. **Observation:** Watch the terminal. The agent will:
   - Log in $\rightarrow$ Search $\rightarrow$ Add to Cart $\rightarrow$ Checkout.
3. **The Approval Gate:** The agent will stop and print `[PAUSE] HUMAN APPROVAL REQUIRED`.
4. **Action:** Type `y` and press Enter.
5. **Result:** Order confirmed. Check the **Dashboard** $\rightarrow$ All steps should be **SUCCESS**.

### Phase 2: The "Break" (Simulating Site Changes)
**Goal:** Prove that when the site changes, the agent doesn't crash—it heals.

1. **The Break:** Open a third terminal and run this command to rename a button ID on the site:
```cmd
curl -X POST http://127.0.0.1:5000/admin/break -H "Content-Type: application/json" -d "{\"type\":\"rename_button\"}"
```
2. **Re-run the Agent:** (Restart `start_core.py`).
3. **The Healing Process:** 
   - The agent will attempt to find the old selector.
   - It will fail.
   - **The Magic:** You will see it trigger the `RecoveryEngine` $\rightarrow$ scan the DOM $\rightarrow$ find a new selector $\rightarrow$ update the `RecipeCache`.
4. **Observation:** The agent recovers and completes the flow.
5. **Result:** Check the **Dashboard** $\rightarrow$ The failed step will now be marked as **RECOVERED** (Yellow).

---

## 🗣️ Key Talking Points for Judges

| When... | Say this... |
|---------|-------------|
| **At the start** | "We've built a self-healing QA agent. Unlike traditional tests that break when a developer changes a single ID, our agent uses a Recovery Engine to adapt in real-time." |
| **During Phase 1** | "The agent follows a predefined recipe. Notice the human-in-the-loop gate at the end—we ensure no actual payments are made without explicit approval." |
| **During the Break** | "I'm now simulating a production change. I've just renamed the button IDs on the backend. A normal test would crash here." |
| **During Recovery** | "Our agent detected the failure, scanned the DOM for similar elements, identified the new correct button, and updated its own memory (the Recipe Cache) so it won't fail again." |
| **Showing Dashboard**| "The dashboard gives us a high-level view of the system's health, highlighting exactly where recoveries happened and how long they took." |

---

## 🚨 Troubleshooting
- **Port Conflict:** If 5000 or 8501 is taken, kill the process or change the port in `app.py`.
- **Agent Hangs:** Ensure you are using `http://127.0.0.1:5000` instead of `localhost` to avoid IPv6 timeouts on Windows.
- **Input not working:** Make sure the terminal running `start_core.py` is the active window when typing `y`.
