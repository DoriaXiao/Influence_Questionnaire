# influence_scoring_app.py
# Run this app with: streamlit run influence_scoring_app.py
# Deploy it on Streamlit Cloud by pushing to GitHub and connecting your repo at https://streamlit.io/cloud
# SHEET_URL = "https://script.google.com/macros/s/AKfycbxM59uBQ5kQ_08-E81gzoOvHGZAYzEzGfp_6jpCZXxXJBNT-KVOV8e8rHtNdnVtDiO1ZA/exec"

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import date, datetime
import os
import requests
import json
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.experimental_guest_login('Login with Google',
                                           provider='google',
                                           oauth2=config['oauth2'])
    authenticator.experimental_guest_login('Login with Microsoft',
                                           provider='microsoft',
                                           oauth2=config['oauth2'])
except Exception as e:
    st.error(e)

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

if 'restart_requested' not in st.session_state:
    st.session_state.restart_requested = False

# --- Navigation ---
def show_progress():
    pages = ["login", "sample_info", "reach", "salience", "discursiveness", "summary"]
    step_labels = {
        "login": "Login",
        "sample_info": "Sample Info",
        "reach": "Reach",
        "salience": "Salience",
        "discursiveness": "Discursiveness",
        "summary": "Submit"
    }
    current = pages.index(st.session_state.page)
    total = len(pages)
    st.markdown(f"#### Step {current + 1} of {total}: {step_labels[st.session_state.page]}")
    st.progress((current + 1) / total)

PAGE_ORDER = ["login", "sample_info", "reach", "salience", "discursiveness", "summary"]

def next_page():
    idx = PAGE_ORDER.index(st.session_state.page)
    if idx < len(PAGE_ORDER) - 1:
        st.session_state.page = PAGE_ORDER[idx + 1]

def prev_page():
    idx = PAGE_ORDER.index(st.session_state.page)
    if idx > 0:
        st.session_state.page = PAGE_ORDER[idx - 1]


def restart_sequence():
    for key in ["sample", "submitted_flag"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.page = 'sample_info'
    st.session_state.restart_requested = False
    st.rerun()  # safe rerun



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

    🔁 *Note:* In order to proceed to the next step for each page/section, please click each button **twice quickly** to advance.
    """)

    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    country = st.radio("Which country are you rating samples for?", ["Tunisia", "Lebanon"])

    if st.button("Continue"):
        if name.strip() == "" or email.strip() == "":
            st.warning("Both name and email are required.")
        else:
            st.session_state.researcher = {"name": name, "email": email}
            st.session_state.country = country
            st.session_state.page = 'sample_info'
            st.rerun()  # ✅ SAFER than st.experimental_rerun()

# Country-specific media sample lists
MEDIA_SAMPLES = {
    "Tunisia": [
        "Midi Show - Mosaique FM", "Huna Tounes - Diwan FM", "Studio Watania - Radio National",
        "RDV9 - Attesia", "Watania News - Watania 1", "Hadath w Tahlil - Watania 1", "Nawaat platform",
        "Alqatiba", "Inqifada", "Legal Agenda", "Wasiat Wsaa - وصية وسع", "Podcast Wqayitk (Alert)",
        "Assabah", "Al Jumhouria", "Al Maghreb", "Presidence Tunisie", "Moncef Marzouki", "Thamer Bdida",
        "Harak 25 Juilia", "Rassd Tunisia", "Haythem El Mekki", "Soumaya Ghanoushi", "Samir Elwafi",
        "Maya Kssouri", "Zied El-Heni", "Olfa Hamdi", "Weather Report (Control Sample)", "La Press",
        "Tunisie Numerique"
    ],
    "Lebanon": [
        "Sar Elwaqt - MTV", "Electing President coverage - MTV", "News bulletin - MTV", "Vision 2030 - LBCI",
        "News bulletin - Al Jadeed", "Niqach - Almayadeen", "Al Haki Be Siase - Voice of Lebanon",
        "Hiwar Masoul", "Bint Jbeil", "Sawt Beirut International", "ALAKHBAR (Newspaper)", "Annahar Newspaper",
        "Legal Agenda", "Daraj Media", "Megaphone", "Political Pen", "Walid Joumblatt", "Samir Geagea",
        "Hosm Matar", "Leila Nicolas", "Ghassan Saoud", "Jamil El Sayyed", "Nawaf Salam", "Radwan Mortada",
        "Weather Report (Control sample)"
    ]
}

# --- Page: Sample Info ---
def page_sample_info():
    show_progress()
    st.title("🎯 Sample Information")

    st.markdown("""
    Please provide information about the media sample you are evaluating.
    Begin by selecting the sample from the dropdown menu below.
    """)

    country = st.session_state.get("country", "Tunisia")  # fallback for safety
    sample_options = MEDIA_SAMPLES.get(country, [])

    selected_sample = st.selectbox(
        "🎬 Select Media Sample (required)",
        sample_options,
        help="Choose the specific TV, radio, newspaper, or social media item from your assignment."
    )

    platform = st.text_input(
        "Platform or Outlet (required)",
        placeholder="e.g., Mosaique FM, Al Jadeed, Facebook page"
    )

    link = st.text_input("Link (if available)", placeholder="Paste the article or video URL")
    transcript = st.text_area("Transcript (paste here if available)")
    pub_date = st.date_input("Air/Publication Date", min_value=date(2024, 1, 1))

    # Save to session state
    st.session_state.sample = {
        "country": country,
        "title": selected_sample,
        "platform": platform,
        "link": link,
        "transcript": transcript,
        "date": pub_date
    }

    if st.button("Next: Reach"):
        if not selected_sample.strip() or not platform.strip():
            st.warning("Please select a media sample and enter the platform or outlet.")
        else:
            next_page()

# --- Page: Reach ---
def page_reach():
    show_progress()

    st.title("📡 Reach")
    st.markdown("""
How many people likely encountered this media content, and how intensively was it seen or heard?

This score estimates **visibility and audience size** — not just raw numbers, but perceived **prominence or amplification**.

Use your local knowledge to judge:
- Was it aired on a national TV or radio station?
- Was it widely shared on social media?
- Was the speaker or platform well-known?
""")

    st.session_state.sample.update({
        "reach_score": st.slider("Reach Score (0–100)", 0, 100, 50),
        "reach_justification": st.text_area(
            "Justification for Reach Score",
            help="Was it on a major TV station? Did it go viral? Is the speaker a well-known figure?"
        )
    })

    if st.button("Next: Salience"):
        if not st.session_state.sample["reach_justification"].strip():
            st.warning("Please justify the Reach score.")
        else:
            next_page()


# --- Page: Salience ---
def page_salience():
    show_progress()

    st.title("🔥 Salience")
    st.markdown("""
How well does this sample reflect the major public issues in Tunisia today?

This measures **topical relevance** — how directly the content speaks to national or civic concerns.
""")

    st.session_state.sample.update({
        "salience_score": st.slider("Salience Score (0–100)", 0, 100, 50),
        "salience_justification": st.text_area(
            "Justification for Salience Score",
            help="Which issues were discussed? How central were they? Was it surface-level or deeply focused?"
        )
    })

    if st.button("Next: Discursiveness"):
        if not st.session_state.sample["salience_justification"].strip():
            st.warning("Please justify the Salience score.")
        else:
            next_page()


# --- Page: Discursiveness ---
def page_discursiveness():
    show_progress()

    st.title("🧠 Discursiveness")
    st.markdown("""
How does the content try to influence opinion?

Evaluate whether it uses **reasoning**, **emotion**, or **credibility** to persuade.
""")

    st.session_state.sample.update({
        "logos_score": st.slider("Logos Score (0–100)", 0, 100, 50,
            help="How much reasoning, structure, or evidence does the content include?"),
        "logos_justification": st.text_area("Logos Justification"),

        "pathos_score": st.slider("Pathos Score (0–100)", 0, 100, 50,
            help="How much emotional appeal is used? (e.g., empathy, outrage, pride)"),
        "pathos_justification": st.text_area("Pathos Justification"),

        "ethos_score": st.slider("Ethos Score (0–100)", 0, 100, 50,
            help="How credible or respected is the speaker or platform in this context?"),
        "ethos_justification": st.text_area("Ethos Justification")
    })

    if st.button("Next: Summary"):
        if not all([
            st.session_state.sample["logos_justification"].strip(),
            st.session_state.sample["pathos_justification"].strip(),
            st.session_state.sample["ethos_justification"].strip()
        ]):
            st.warning("All three justifications (Logos, Pathos, Ethos) are required.")
        else:
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
    st.markdown("#### Researcher Info")
    st.text(f"Name: {sample['researcher']['name']}")
    st.text(f"Email: {sample['researcher']['email']}")
    
    st.markdown("#### Scores & Justifications")
    for key, value in sample.items():
        if key == "researcher":
            continue
        if "_score" in key:
            label = key.replace("_score", "").replace("_", " ").title()
            st.markdown(f"**{label}**: {value}")
        elif "_justification" in key:
            label = key.replace("_justification", "").replace("_", " ").title()
            st.markdown(f"📝 *{label} Justification*: {value}")


    if st.button("Submit"):
        st.session_state.responses.append(sample)
        submitted = submit_to_google_sheet(sample)
        if submitted:
            st.success("Sample submitted to Google Sheet!")
            st.session_state.submitted_flag = True

    if st.session_state.get("submitted_flag"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Evaluate Another Sample"):
                st.session_state.restart_requested = True
                st.session_state.submitted_flag = False
        with col2:
            if st.button("🚪 I’ve Completed All My Samples"):
                st.session_state.page = 'thank_you'
                st.session_state.submitted_flag = False


# --- Handle restart request ---
if st.session_state.get('restart_requested', False):
    restart_sequence()

# --- Page: Thank You ---
def page_thank_you():
    st.title("🎉 Thank you for your contributions!")
    st.markdown("""
    We truly appreciate your thoughtful analysis and time. Your responses have been recorded.

    If you have any questions or would like to follow up, please contact the research team.

    ✅ You may now close this tab or exit the application.
    """)

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
elif st.session_state.page == 'summary':
    page_summary()
elif st.session_state.page == 'thank_you':
    page_thank_you()
