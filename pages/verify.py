"""
pages/verify.py
The main verification flow:
  1. Enter student info + subjects/marks
  2. Upload marksheet (PDF or image)
  3. Run extraction + comparison
  4. Show diff report
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.extractor import extract_from_uploaded_file
from utils.comparator import compare
from utils.storage import save_record, report_dict_from_report


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_api_key() -> str | None:
    key = st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
    return key.strip() if key else None


def status_badge(status: str) -> str:
    if status == "verified":
        return '<span class="badge-verified">✓ Verified</span>'
    elif status == "flagged":
        return '<span class="badge-flagged">⚑ Flagged — manual review required</span>'
    elif status == "warning":
        return '<span class="badge-warning">⚠ Warning — some subjects grade-only</span>'
    return '<span class="badge-flagged">⚠ Error</span>'


def subject_row_html(r) -> str:
    if r.status == "match":
        marks_entered = int(r.marks_entered) if r.marks_entered == int(r.marks_entered) else r.marks_entered
        marks_extracted = int(r.marks_extracted) if r.marks_extracted == int(r.marks_extracted) else r.marks_extracted
        return f"""
        <tr>
          <td>{r.subject_entered}</td>
          <td class="mono">{marks_entered}</td>
          <td class="mono">{marks_extracted}</td>
          <td class="diff-match">✓ Match</td>
        </tr>"""
    elif r.status == "mismatch":
        delta_str = f"{r.delta:+.0f}" if r.delta is not None else "—"
        marks_entered = int(r.marks_entered) if r.marks_entered == int(r.marks_entered) else r.marks_entered
        marks_extracted = int(r.marks_extracted) if r.marks_extracted == int(r.marks_extracted) else r.marks_extracted
        return f"""
        <tr class="diff-mismatch">
          <td>{r.subject_entered}</td>
          <td class="mono">{marks_entered}</td>
          <td class="mono">{marks_extracted}</td>
          <td class="diff-mismatch">✗ Mismatch ({delta_str})</td>
        </tr>"""
    elif r.status == "not_found":
        return f"""
        <tr>
          <td>{r.subject_entered}</td>
          <td class="mono">{r.marks_entered if r.marks_entered is not None else "—"}</td>
          <td class="mono diff-missing">Not found</td>
          <td class="diff-missing">Not in marksheet</td>
        </tr>"""
    elif r.status == "grade_only":
        return f"""
        <tr>
          <td>{r.subject_entered}</td>
          <td class="mono">{r.marks_entered if r.marks_entered is not None else "—"}</td>
          <td class="mono diff-missing">Grade only</td>
          <td class="badge-warning" style="font-size:0.8rem;">Grade — no marks</td>
        </tr>"""
    return ""


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    api_key = get_api_key()

    if not api_key:
        st.warning("⚙️ Add your Gemini API key in **Settings** before verifying.", icon="🔑")
        return

    # ── Step 1: Student info ──────────────────────────────────────────────────
    st.markdown('<div class="section-eyebrow">Step 1 — Student details</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1:
        student_name = st.text_input("Full name (as on marksheet)", placeholder="e.g. Priya Ramesh")
    with col2:
        roll_number = st.text_input("Roll / register number", placeholder="e.g. 1234567")
    with col3:
        exam_class = st.selectbox("Class", ["10 (SSLC)", "12 (PUC / HSC)"])

    board = st.text_input("Board", placeholder="e.g. CBSE, Karnataka SSLC, Maharashtra SSC")

    st.markdown("---")

    # ── Step 2: Subject entry ─────────────────────────────────────────────────
    st.markdown('<div class="section-eyebrow">Step 2 — Entered marks</div>', unsafe_allow_html=True)
    st.caption("Add each subject and the marks as claimed in the application form.")

    if "subjects" not in st.session_state:
        st.session_state.subjects = [{"name": "", "marks": ""}]

    def add_subject():
        st.session_state.subjects.append({"name": "", "marks": ""})

    def remove_subject(i):
        st.session_state.subjects.pop(i)

    for i, subj in enumerate(st.session_state.subjects):
        c1, c2, c3 = st.columns([3, 1.5, 0.4])
        with c1:
            st.session_state.subjects[i]["name"] = st.text_input(
                "Subject", value=subj["name"],
                key=f"sname_{i}", label_visibility="collapsed",
                placeholder=f"Subject {i+1} (e.g. Mathematics)"
            )
        with c2:
            st.session_state.subjects[i]["marks"] = st.text_input(
                "Marks", value=subj["marks"],
                key=f"smarks_{i}", label_visibility="collapsed",
                placeholder="Marks"
            )
        with c3:
            if len(st.session_state.subjects) > 1:
                st.button("✕", key=f"del_{i}", on_click=remove_subject, args=(i,))

    st.button("＋ Add subject", on_click=add_subject)

    # Tolerance setting
    tolerance = st.slider(
        "Allowed marks difference (tolerance)",
        min_value=0, max_value=5, value=0,
        help="Flag if extracted marks differ from entered marks by more than this."
    )

    st.markdown("---")

    # ── Step 3: Upload marksheet ──────────────────────────────────────────────
    st.markdown('<div class="section-eyebrow">Step 3 — Upload marksheet</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload marksheet (PDF or image)",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Accepts scanned PDFs, photos, or digital marksheets from any board."
    )

    if uploaded:
        st.success(f"📄 {uploaded.name} uploaded — ready to verify")

    st.markdown("---")

    # ── Verify button ─────────────────────────────────────────────────────────
    run_disabled = not uploaded or not any(s["name"] for s in st.session_state.subjects)

    if st.button("🔍  Verify marksheet", type="primary", disabled=run_disabled, use_container_width=True):
        _run_verification(
            api_key, student_name, roll_number, exam_class, board,
            uploaded, tolerance
        )


def _run_verification(api_key, student_name, roll_number, exam_class, board, uploaded, tolerance):
    # Build form JSON
    subjects_dict = {}
    for s in st.session_state.subjects:
        name = s["name"].strip()
        marks_raw = s["marks"].strip()
        if name:
            try:
                subjects_dict[name] = float(marks_raw) if marks_raw else None
            except ValueError:
                subjects_dict[name] = None

    form_data = {
        "student_name": student_name.strip() or None,
        "roll_number": roll_number.strip() or None,
        "subjects": subjects_dict,
    }

    # Extract
    with st.spinner("🔍 Sending to Gemini Vision…"):
        try:
            extracted, preview_img = extract_from_uploaded_file(uploaded, api_key)
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            return

    # Compare
    report = compare(form_data, extracted, tolerance=tolerance)

    # Save
    record_id = save_record(
        applicant_name=student_name or "Unknown",
        roll=roll_number or "—",
        board=extracted.get("board") or board or "—",
        exam_class=exam_class,
        form_data=form_data,
        extracted=extracted,
        report_dict=report_dict_from_report(report),
        overall_status=report.overall_status,
    )

    # ── Show results ──────────────────────────────────────────────────────────
    st.markdown("## Verification result")
    st.markdown(f'Record ID: <span class="mono">{record_id}</span>', unsafe_allow_html=True)
    st.markdown(status_badge(report.overall_status), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_img, col_meta = st.columns([1, 1.6])

    with col_img:
        st.image(preview_img, caption="Uploaded marksheet (page 1)", use_container_width=True)

    with col_meta:
        st.markdown('<div class="section-eyebrow">Extracted metadata</div>', unsafe_allow_html=True)
        meta_rows = [
            ("Student name", extracted.get("student_name") or "—"),
            ("Roll number",  extracted.get("roll_number") or "—"),
            ("Board",        extracted.get("board") or "—"),
            ("Year",         extracted.get("exam_year") or "—"),
            ("Result",       extracted.get("result") or "—"),
        ]
        for label, val in meta_rows:
            c1, c2 = st.columns([1, 1.5])
            c1.caption(label)
            c2.write(val)

        match_pct = int(report.match_rate * 100)
        st.progress(report.match_rate, text=f"Match rate: {match_pct}%")

    # Subject diff table
    st.markdown("### Subject comparison")

    rows_html = "".join(subject_row_html(r) for r in report.subject_results)
    st.markdown(f"""
    <table class="diff-table">
      <thead><tr>
        <th>Subject (entered)</th>
        <th>Entered marks</th>
        <th>Extracted marks</th>
        <th>Status</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Raw extracted JSON expandable
    with st.expander("Raw extracted JSON"):
        st.json(extracted)

    if report.overall_status == "verified":
        st.success("✅ All subjects match. This application can proceed to the next stage.")
    elif report.overall_status == "flagged":
        st.error(
            f"⚑ {len(report.flagged_subjects)} subject(s) flagged. "
            "Please queue this application for manual review before proceeding."
        )
    elif report.overall_status == "warning":
        st.warning("⚠ Some subjects returned grade-only data. Manual check recommended for these subjects.")
