import streamlit as st
import json
import os
import glob
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Self-Healing QA Agent Dashboard", layout="wide")

st.title("Self-Healing QA Agent Dashboard")
st.markdown("Real-time timeline of QA agent runs, failures, and recoveries")

dashboard_dir = os.path.dirname(os.path.abspath(__file__))
log_files = sorted(glob.glob(os.path.join(dashboard_dir, "..", "logs", "*.json")), key=os.path.getmtime, reverse=True)

if not log_files:
    st.info("No run logs found yet. Run the agent to see results here.")
    st.stop()

selected_log = st.sidebar.selectbox("Select Run", log_files, format_func=lambda x: os.path.basename(x))

with open(selected_log, 'r') as f:
    logs = json.load(f)

run_id = logs[0]['run_id'] if logs else "Unknown"
st.sidebar.markdown(f"**Run ID:** `{run_id}`")

status_colors = {
    "success": "SUCCESS",
    "fail": "FAIL",
    "recovered": "RECOVERED",
    "approval_pending": "PENDING",
    "approved": "APPROVED"
}

status_labels = {
    "success": "Success",
    "fail": "Failed",
    "recovered": "Recovered",
    "approval_pending": "Awaiting Approval",
    "approved": "Approved"
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Steps", len(logs))
with col2:
    success_count = sum(1 for l in logs if l['status'] == 'success')
    st.metric("Successful", success_count)
with col3:
    recovered_count = sum(1 for l in logs if l['status'] == 'recovered')
    st.metric("Recovered", recovered_count)
with col4:
    fail_count = sum(1 for l in logs if l['status'] == 'fail')
    st.metric("Failed", fail_count)

st.markdown("---")

st.subheader("Execution Timeline")

for i, log in enumerate(logs):
    status = log['status']
    icon = status_colors.get(status, "UNKNOWN")
    label = status_labels.get(status, status)
    
    with st.container():
        cols = st.columns([1, 3, 2, 2])
        
        with cols[0]:
            st.markdown(f"### {icon}")
        
        with cols[1]:
            st.markdown(f"**Step {i+1}: {log['step']}**")
            st.caption(f"Status: {label}")
        
        with cols[2]:
            ts = log['timestamp']
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                st.caption(f"Time: {dt.strftime('%H:%M:%S')}")
            except:
                st.caption(f"Time: {ts}")
            
            if log.get('recovery_duration_ms'):
                st.caption(f"Recovery: {log['recovery_duration_ms']}ms")
        
        with cols[3]:
            if log.get('detection_reason'):
                st.error(f"Reason: {log['detection_reason']}")
            if log.get('recovery_action'):
                st.success(f"Action: {log['recovery_action']}")
        
        with st.expander("Details"):
            if log.get('data'):
                st.json(log['data'])
            if log.get('error'):
                st.code(log['error'])
            if log.get('old_selector') or log.get('new_selector'):
                col_old, col_new = st.columns(2)
                with col_old:
                    st.markdown("**Old Selector**")
                    st.code(log.get('old_selector', 'N/A'))
                with col_new:
                    st.markdown("**New Selector**")
                    st.code(log.get('new_selector', 'N/A'))
        
        st.markdown("---")

st.markdown("---")
st.subheader("Raw Log Data")
st.json(logs)

if st.button("Refresh"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Legend")
for status, icon in status_colors.items():
    st.sidebar.markdown(f"{icon} {status_labels[status]}")