"""
utils/storage.py
Simple file-based persistence for verification records.
Each record is a JSON file under data/records/.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "records"


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_record(
    applicant_name: str,
    roll: str,
    board: str,
    exam_class: str,
    form_data: dict,
    extracted: dict,
    report_dict: dict,
    overall_status: str,
) -> str:
    """Persist a verification run and return its record ID."""
    _ensure_dir()
    record_id = str(uuid.uuid4())[:8].upper()
    record = {
        "id": record_id,
        "timestamp": datetime.now().isoformat(),
        "applicant_name": applicant_name,
        "roll": roll,
        "board": board,
        "exam_class": exam_class,
        "form_data": form_data,
        "extracted": extracted,
        "report": report_dict,
        "overall_status": overall_status,
    }
    path = DATA_DIR / f"{record_id}.json"
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    return record_id


def load_all_records() -> list[dict]:
    """Return all records sorted by timestamp desc."""
    _ensure_dir()
    records = []
    for path in DATA_DIR.glob("*.json"):
        try:
            with open(path) as f:
                records.append(json.load(f))
        except Exception:
            pass
    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return records


def load_record(record_id: str) -> dict | None:
    path = DATA_DIR / f"{record_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def report_dict_from_report(report) -> dict:
    """Serialise a ComparisonReport to a plain dict for JSON storage."""
    return {
        "student_name_entered": report.student_name_entered,
        "student_name_extracted": report.student_name_extracted,
        "roll_entered": report.roll_entered,
        "roll_extracted": report.roll_extracted,
        "board_extracted": report.board_extracted,
        "exam_year_extracted": report.exam_year_extracted,
        "overall_status": report.overall_status,
        "match_rate": report.match_rate,
        "subject_results": [
            {
                "subject_entered": r.subject_entered,
                "subject_matched": r.subject_matched,
                "marks_entered": r.marks_entered,
                "marks_extracted": r.marks_extracted,
                "status": r.status,
                "delta": r.delta,
            }
            for r in report.subject_results
        ],
    }
