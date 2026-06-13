"""
pages/results.py
College admin view: list of all past verification records,
with status filtering and per-record detail drill-down.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.storage import load_all_records, load_record


STATUS_EMOJI = {
    "verified": "✓",
    "flagged":  "⚑",
    "warning":  "⚠",
    "error":    "✗",
}

STATUS_COLOR = {
    "verified": "#1a7a4a",
    "flagged":  "#b91c1c",
    "warning":  "#92400e",
    "error":    "#6b7280",
}


def render():
    records = load_all_records()

    st.markdown("## Verification records")

    if not records:
        st.info("No verifications run yet. Go to **Enter marks** to verify your first marksheet.")
        return

    #  Filters 
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox("Filter by status", ["All", "verified", "flagged", "warning"])
    with col2:
        search = st.text_input("Search by name / roll / board", placeholder="Type to filter…")

    filtered = records
    if status_filter != "All":
        filtered = [r for r in filtered if r.get("overall_status") == status_filter]
    if search:
        q = search.lower()
        filtered = [
            r for r in filtered
            if q in (r.get("applicant_name") or "").lower()
            or q in (r.get("roll") or "").lower()
            or q in (r.get("board") or "").lower()
        ]

    st.caption(f"Showing {len(filtered)} of {len(records)} records")
    st.markdown("---")

    #  Summary cards 
    total     = len(records)
    verified  = sum(1 for r in records if r.get("overall_status") == "verified")
    flagged   = sum(1 for r in records if r.get("overall_status") == "flagged")
    warnings  = sum(1 for r in records if r.get("overall_status") == "warning")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", total)
    m2.metric("✓ Verified", verified)
    m3.metric("⚑ Flagged", flagged)
    m4.metric("⚠ Warnings", warnings)

    st.markdown("---")

    #  Record list 
    if "open_record" not in st.session_state:
        st.session_state.open_record = None

    for rec in filtered:
        status = rec.get("overall_status", "error")
        color  = STATUS_COLOR.get(status, "#6b7280")
        emoji  = STATUS_EMOJI.get(status, "?")
        ts     = rec.get("timestamp", "")[:16].replace("T", " ")
        match_rate = rec.get("report", {}).get("match_rate", None)
        match_str  = f"{int(match_rate*100)}%" if match_rate is not None else "—"

        col_status, col_name, col_board, col_match, col_ts, col_btn = st.columns([0.5, 2, 2, 1, 1.5, 1])

        col_status.markdown(
            f'<span style="color:{color}; font-size:1.1rem; font-weight:600;">{emoji}</span>',
            unsafe_allow_html=True
        )
        col_name.write(f"**{rec.get('applicant_name','—')}**  \n`{rec.get('roll','—')}`")
        col_board.write(f"{rec.get('board','—')}  \n{rec.get('exam_class','')}")
        col_match.write(match_str)
        col_ts.caption(ts)

        rec_id = rec["id"]
        if col_btn.button("View", key=f"view_{rec_id}"):
            st.session_state.open_record = rec_id if st.session_state.open_record != rec_id else None
            st.rerun()

        # Inline detail panel
        if st.session_state.open_record == rec_id:
            _render_detail(rec)

        st.divider()


def _render_detail(rec: dict):
    """Inline expanded detail for a record."""
    report = rec.get("report", {})
    extracted = rec.get("extracted", {})

    with st.container():
        st.markdown(f"#### Record `{rec['id']}` — detail")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-eyebrow">Entered</div>', unsafe_allow_html=True)
            st.write(f"**Name:** {report.get('student_name_entered') or '—'}")
            st.write(f"**Roll:** {report.get('roll_entered') or '—'}")

        with c2:
            st.markdown('<div class="section-eyebrow">Extracted from marksheet</div>', unsafe_allow_html=True)
            st.write(f"**Name:** {report.get('student_name_extracted') or '—'}")
            st.write(f"**Roll:** {report.get('roll_extracted') or '—'}")
            st.write(f"**Board:** {report.get('board_extracted') or '—'}")
            st.write(f"**Year:** {report.get('exam_year_extracted') or '—'}")

        st.markdown("**Subject comparison**")
        subject_results = report.get("subject_results", [])
        if subject_results:
            rows = ""
            for r in subject_results:
                s = r["status"]
                if s == "match":
                    me = int(r["marks_entered"]) if r["marks_entered"] is not None and float(r["marks_entered"]) == int(float(r["marks_entered"])) else r["marks_entered"]
                    mx = int(r["marks_extracted"]) if r["marks_extracted"] is not None and float(r["marks_extracted"]) == int(float(r["marks_extracted"])) else r["marks_extracted"]
                    rows += f'<tr><td>{r["subject_entered"]}</td><td class="mono">{me}</td><td class="mono">{mx}</td><td class="diff-match">✓</td></tr>'
                elif s == "mismatch":
                    delta = r.get("delta")
                    ds = f"{delta:+.0f}" if delta is not None else "—"
                    rows += f'<tr class="diff-mismatch"><td>{r["subject_entered"]}</td><td class="mono">{r["marks_entered"]}</td><td class="mono">{r["marks_extracted"]}</td><td class="diff-mismatch">✗ {ds}</td></tr>'
                else:
                    rows += f'<tr><td>{r["subject_entered"]}</td><td class="mono">{r["marks_entered"] or "—"}</td><td class="mono diff-missing">{s}</td><td class="diff-missing">{s}</td></tr>'

            st.markdown(f"""
            <table class="diff-table">
              <thead><tr>
                <th>Subject</th><th>Entered</th><th>Extracted</th><th>Status</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>""", unsafe_allow_html=True)
        else:
            st.caption("No subject data.")

        with st.expander("Raw extracted JSON"):
            st.json(extracted)
