# influence_scoring_app.py
# Run this app with: streamlit run influence_scoring_app.py
# Deploy it on Streamlit Cloud by pushing to GitHub and connecting your repo at https://streamlit.io/cloud

import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Influence Scoring App", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400&display=swap');
html, body, [class*='css']  { font-family: 'Lato', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
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

# --- Page: Login ---
def page_login():
    st.title("🔐 Researcher Login")
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    if st.button("Continue") and name and email:
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
        next_page()

# --- Page: Reach ---
def page_reach():
    st.title("📡 Reach")
    st.session_state.sample.update({
        "reach_score": st.slider("Reach Score (1–100)", 0, 100, 50),
        "reach_justification": st.text_area("Justify your Reach score")
    })
    if st.button("Next: Salience"):
        next_page()

# --- Page: Salience ---
def page_salience():
    st.title("🔥 Salience")
    st.session_state.sample.update({
        "salience_score": st.slider("Salience Score (1–100)", 0, 100, 50),
        "salience_justification": st.text_area("Justify your Salience score")
    })
    if st.button("Next: Discursiveness"):
        next_page()

# --- Page: Discursiveness ---
def page_discursiveness():
    st.title("🧠 Discursiveness")
    st.session_state.sample.update({
        "logos_score": st.slider("Logos (Reasoning) Score", 0, 100, 50),
        "logos_justification": st.text_area("Justify Logos score"),
        "pathos_score": st.slider("Pathos (Emotion) Score", 0, 100, 50),
        "pathos_justification": st.text_area("Justify Pathos score"),
        "ethos_score": st.slider("Ethos (Credibility) Score", 0, 100, 50),
        "ethos_justification": st.text_area("Justify Ethos score")
    })
    if st.button("Next: Democratic Values"):
        next_page()

# --- Page: Values ---
def page_values():
    st.title("🏛️ Democratic Values (Score + Justification)")
    for value in [
        "Common Concern", "Aired Arenas", "Pluralism", "Truth",
        "Civility", "Equal Opportunity", "Efficacy"]:
        st.session_state.sample[value + "_score"] = st.slider(f"{value} Score", 0, 100, 50, key=value)
        st.session_state.sample[value + "_justification"] = st.text_area(f"Justify {value}", key=value+'_txt')
    if st.button("Next: Summary"):
        next_page()

# --- Save to CSV ---
def save_to_csv(entry, path="responses.csv"):
    df = pd.DataFrame([entry])
    if not os.path.exists(path):
        df.to_csv(path, index=False)
    else:
        df.to_csv(path, mode='a', header=False, index=False)

# --- Page: Summary ---
def page_summary():
    st.title("📊 Submission Summary")
    sample = st.session_state.sample
    sample["researcher"] = st.session_state.researcher
    st.write(sample)

    if st.button("Submit"):
        st.session_state.responses.append(sample)
        save_to_csv(sample)  # persist to CSV
        st.success("Sample submitted! You can now score a new sample.")
        st.session_state.page = 'sample_info'

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
