# influence_scoring_app.py
# Run this app with: streamlit run influence_scoring_app.py
# Deploy it on Streamlit Cloud by pushing to GitHub and connecting your repo at https://streamlit.io/cloud
# SHEET_URL = "https://script.google.com/macros/s/AKfycbxM59uBQ5kQ_08-E81gzoOvHGZAYzEzGfp_6jpCZXxXJBNT-KVOV8e8rHtNdnVtDiO1ZA/exec"

import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import requests
import json

st.set_page_config(page_title="Influence Scoring App", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400&display=swap');
html, body, [class*='css']  {
    font-family: 'Lato', sans-serif;
    background-color: #f5f7fa;
    color: #1a1a1a;
}
.block-container {
    padding: 2rem 2rem;
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.05);
    max-width: 900px;
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'login'

if 'responses' not in st.session_state:
    st.session_state.responses = []

# --- Navigation ---
def next_page():
    pages = ["login", "sample_info", "reach", "salience", "discursiveness", "values", "summary"]
    idx = pages.index(st.session_state.page)
    if idx < len(pages) - 1:
        st.session_state.page = pages[idx + 1]

def restart_sequence():
    st.session_state.page = 'sample_info'
    st.session_state.sample = {}

# --- Page: Login ---
def page_login():
    st.title("🔐 Researcher Login")
    st.markdown("""
    Welcome to the **Tunisia Media Influence Scoring Questionnaire**.
    
    This form is part of the *Public Sphere Index* initiative. You’ll assess each media sample using your own informed judgment — no specific data or research is required.

    You’ll evaluate:
    - **Reach** – How widely was this sample seen or shared?
    - **Salience** – How well does it reflect Tunisia’s top public concerns?
    - **Discursiveness** – Does it use reasoning, emotion, or credibility to persuade?

    **Score each dimension from 0 to 100.**
    
    🟢 *There are no right or wrong answers. Your thoughtful judgment is what matters most.*
    """)
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    if st.button("Continue"):
        if name.strip() == "" or email.strip() == "":
            st.warning("Both name and email are required.")
        else:
            st.session_state.researcher = {"name": name, "email": email}
            st.session_state.page = 'sample_info'

# --- Page: Sample Info ---
def page_sample_info():
    st.title("🎯 Sample Information")
    st.session_state.sample = {
        "title": st.text_input("Media Title or Description"),
        "platform": st.text_input("Platform or Outlet"),
        "link": st.text_input("Link (if available)"),
        "transcript": st.text_area("Transcript (paste here if available)"),
        "date": st.date_input("Air/Publication Date", min_value=date(2024, 1, 1))
    }
    if st.button("Next: Reach"):
        if not st.session_state.sample["title"].strip() or not st.session_state.sample["platform"].strip():
            st.warning("Media title and platform are required.")
        else:
            next_page()

# --- Page: Reach ---
def page_reach():
    st.title("📡 Reach")
    st.markdown("""
    **Reach** estimates how widely the sample was encountered — not just in raw numbers, but in visibility and amplification.

    Ask yourself:
    - Was it broadcast nationally?
    - Was it viral on social media?
    - Was the platform or speaker well-known?
    """)
    st.session_state.sample.update({
        "reach_score": st.slider("Reach Score (1–100)", 0, 100, 50),
        "reach_justification": st.text_area("Justify your Reach score")
    })
    if st.button("Next: Salience"):
        if not st.session_state.sample["reach_justification"].strip():
            st.warning("Please justify the Reach score.")
        else:
            next_page()

# --- Page: Salience ---
def page_salience():
    st.title("🔥 Salience")
    st.markdown("""
    **Salience** measures how well the content reflects key public concerns in Tunisia today.

    Think about:
    - Which issues were addressed?
    - How central were they?
    - Was the coverage superficial or in-depth?
    """)
    st.session_state.sample.update({
        "salience_score": st.slider("Salience Score (1–100)", 0, 100, 50),
        "salience_justification": st.text_area("Justify your Salience score")
    })
    if st.button("Next: Discursiveness"):
        if not st.session_state.sample["salience_justification"].strip():
            st.warning("Please justify the Salience score.")
        else:
            next_page()

# --- Page: Discursiveness ---
def page_discursiveness():
    st.title("🧠 Discursiveness")
    st.markdown("""
    **Discursiveness** is about how the content attempts to influence opinion through:
    - **Logos**: reasoning, evidence, and structure
    - **Pathos**: emotional appeal (e.g., empathy, fear, pride)
    - **Ethos**: the credibility or authority of the speaker/platform
    """)
    st.session_state.sample.update({
        "logos_score": st.slider("Logos (Reasoning) Score", 0, 100, 50),
        "logos_justification": st.text_area("Justify Logos score"),
        "pathos_score": st.slider("Pathos (Emotion) Score", 0, 100, 50),
        "pathos_justification": st.text_area("Justify Pathos score"),
        "ethos_score": st.slider("Ethos (Credibility) Score", 0, 100, 50),
        "ethos_justification": st.text_area("Justify Ethos score")
    })
    if st.button("Next: Democratic Values"):
        if not all([
            st.session_state.sample["logos_justification"].strip(),
            st.session_state.sample["pathos_justification"].strip(),
            st.session_state.sample["ethos_justification"].strip()
        ]):
            st.warning("All three justifications (Logos, Pathos, Ethos) are required.")
        else:
            next_page()


# --- Page: Values ---
def page_values():
    st.title("🏛️ Democratic Values (Score + Justification)")
    valid = True
    for value in [
        "Common Concern", "Aired Arenas", "Pluralism", "Truth",
        "Civility", "Equal Opportunity", "Efficacy"]:
        st.session_state.sample[value + "_score"] = st.slider(f"{value} Score", 0, 100, 50, key=value)
        st.session_state.sample[value + "_justification"] = st.text_area(f"Justify {value}", key=value+'_txt')

    if st.button("Next: Summary"):
        for value in [
            "Common Concern", "Aired Arenas", "Pluralism", "Truth",
            "Civility", "Equal Opportunity", "Efficacy"]:
            if not st.session_state.sample[value + "_justification"].strip():
                st.warning(f"Justification for '{value}' is required.")
                valid = False
                break
        if valid:
            next_page()

# --- Submit to Google Sheet ---
def submit_to_google_sheet(data):
    SHEET_URL = "https://script.google.com/macros/s/AKfycbxM59uBQ5kQ_08-E81gzoOvHGZAYzEzGfp_6jpCZXxXJBNT-KVOV8e8rHtNdnVtDiO1ZA/exec"
    try:
        serializable_data = {
            k: (v.isoformat() if isinstance(v, (date, datetime)) else v)
            for k, v in data.items()
        }
        response = requests.post(SHEET_URL, json=serializable_data)
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# --- Page: Summary ---
def page_summary():
    st.markdown("""
    ### ✅ All done with this media sample!
    
    If you're ready, please continue by evaluating another sample. Click the button below and enter the next piece of content you’ve been assigned.
    
    🔁 This helps ensure consistent scoring across your assigned set.
    """)
    st.title("📊 Submission Summary")
    sample = st.session_state.sample
    sample["researcher"] = st.session_state.researcher
    st.write(sample)

    if st.button("Submit"):
        st.session_state.responses.append(sample)
        submitted = submit_to_google_sheet(sample)
        if submitted:
            st.success("Sample submitted to Google Sheet!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Evaluate Another Sample"):
                    restart_sequence()
            with col2:
                if st.button("🚪 I’ve Completed All My Samples"):
                    st.markdown("### 🎉 Thank you!
Your submissions are complete. You may now close this tab.")
        else:
            st.error("Submission failed.")

# --- Page Routing ---
if st.session_state.page == 'login':
    page_login()
elif st.session_state.page == 'sample_info':
    page_sample_info()
elif st.session_state.page == 'reach':
    page_reach()
elif st.session_state.page == 'salience':
    page_salience()
elif st.session_state.page == 'discursiveness':
    page_discursiveness()
elif st.session_state.page == 'values':
    page_values()
elif st.session_state.page == 'summary':
    page_summary()

