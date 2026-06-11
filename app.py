import streamlit as st

st.set_page_config(
    page_title="DigiCert — Marksheet Verifier",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject global styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* Global card style */
.dc-card {
    background: #ffffff;
    border: 1px solid #e8e6e1;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Status badges */
.badge-verified {
    display: inline-flex; align-items: center; gap: 6px;
    background: #edfaf3; color: #1a7a4a;
    border: 1px solid #a3e4c1;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.82rem; font-weight: 500;
}
.badge-flagged {
    display: inline-flex; align-items: center; gap: 6px;
    background: #fff4f4; color: #b91c1c;
    border: 1px solid #fca5a5;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.82rem; font-weight: 500;
}
.badge-warning {
    display: inline-flex; align-items: center; gap: 6px;
    background: #fffbeb; color: #92400e;
    border: 1px solid #fcd34d;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.82rem; font-weight: 500;
}

/* Diff table */
.diff-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.diff-table th {
    background: #f7f6f3; color: #6b6860;
    font-weight: 500; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 0.04em;
    padding: 8px 12px; text-align: left;
    border-bottom: 1px solid #e8e6e1;
}
.diff-table td { padding: 10px 12px; border-bottom: 1px solid #f0eeea; }
.diff-table tr:last-child td { border-bottom: none; }
.diff-match { color: #1a7a4a; font-weight: 500; }
.diff-mismatch { color: #b91c1c; font-weight: 500; background: #fff9f9; }
.diff-missing { color: #92400e; font-style: italic; }

/* Section header */
.section-eyebrow {
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: #9b8ea0; margin-bottom: 0.4rem;
}

/* Mono for JSON / values */
.mono { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }

/* Top nav bar */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.75rem 0; margin-bottom: 2rem;
    border-bottom: 1px solid #e8e6e1;
}
.topbar-brand {
    font-size: 1.1rem; font-weight: 600; color: #1a1816;
    display: flex; align-items: center; gap: 8px;
}
.topbar-brand span { color: #6c4de6; }

/* Step indicator */
.steps { display: flex; gap: 0; margin-bottom: 2rem; }
.step {
    flex: 1; padding: 10px 16px;
    font-size: 0.82rem; font-weight: 500;
    border-bottom: 2px solid #e8e6e1;
    color: #9b9590;
}
.step.active { border-bottom-color: #6c4de6; color: #6c4de6; }
.step.done { border-bottom-color: #1a7a4a; color: #1a7a4a; }
</style>
""", unsafe_allow_html=True)

# Top nav
st.markdown("""
<div class="topbar">
    <div class="topbar-brand">
        🎓 Digi<span>Cert</span>
    </div>
    <div style="font-size:0.8rem; color:#9b9590;">Marksheet verification for college admissions</div>
</div>
""", unsafe_allow_html=True)

# Navigation via session state
if "page" not in st.session_state:
    st.session_state.page = "verify"

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("📋  Enter marks", use_container_width=True,
                 type="primary" if st.session_state.page == "verify" else "secondary"):
        st.session_state.page = "verify"
        st.rerun()
with col2:
    if st.button("📁  View results", use_container_width=True,
                 type="primary" if st.session_state.page == "results" else "secondary"):
        st.session_state.page = "results"
        st.rerun()
with col3:
    if st.button("⚙️  Settings", use_container_width=True,
                 type="primary" if st.session_state.page == "settings" else "secondary"):
        st.session_state.page = "settings"
        st.rerun()

st.markdown("---")

# Route to pages
if st.session_state.page == "verify":
    from pages.verify import render
    render()
elif st.session_state.page == "results":
    from pages.results import render
    render()
elif st.session_state.page == "settings":
    from pages.settings import render
    render()
