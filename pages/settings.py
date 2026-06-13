"""
pages/settings.py
API key configuration and app-level preferences.
"""

import streamlit as st
import os


def render():
    st.markdown("## Settings")

    st.markdown('<div class="section-eyebrow">Gemini API key</div>', unsafe_allow_html=True)
    st.caption(
        "Required for VLM extraction. Get your key at "
        "[Google AI Studio](https://aistudio.google.com/app/apikey). "
        "The key is stored in session memory only and never persisted to disk."
    )

    current = st.session_state.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))
    new_key = st.text_input(
        "API key",
        value=current,
        type="password",
        placeholder="API KEY HERE",
    )

    if st.button("Save API key", type="primary"):
        st.session_state["gemini_api_key"] = new_key.strip()
        st.success("API key saved for this session.")

    st.markdown("---")

    st.markdown('<div class="section-eyebrow">Default verification settings</div>', unsafe_allow_html=True)

    default_tolerance = st.slider(
        "Default marks tolerance",
        min_value=0, max_value=5, value=0,
        help="How many marks difference is acceptable before flagging. 0 = exact match required."
    )
    st.session_state["default_tolerance"] = default_tolerance

    st.markdown("---")

    st.markdown('<div class="section-eyebrow">About DigiCert</div>', unsafe_allow_html=True)
    st.markdown("""
DigiCert automates the first pass of marksheet verification for college admissions.

**How it works:**
1. Applicant enters their subjects and marks in the form
2. They upload their physical marksheet (PDF or photo — any board, any language)
3. Gemini Vision extracts the structured data from the marksheet
4. The system compares entered vs extracted marks subject-by-subject
5. Exact matches are auto-approved; discrepancies are flagged for manual review

**Supported boards:** All Indian boards — CBSE, ICSE, Karnataka SSLC/PUC, Maharashtra SSC/HSC, Tamil Nadu SSLC/HSC, AP/Telangana, Kerala, UP, Rajasthan, and more. Regional language marksheets are supported via Gemini's multilingual vision capability.

**DigiLocker note:** CBSE and most major state boards are on DigiLocker. For students with DigiLocker-verified PDFs, no separate upload is needed — the PDF already carries board-issued metadata. DigiLocker integration as a direct pull path is planned for a future release.

---
Built with Streamlit + Gemini Vision API.
    """)
