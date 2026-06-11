"""
utils/comparator.py
Compares form-entered JSON with VLM-extracted JSON.
Returns a structured diff report with per-field verdicts.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


# ── Subject name normalisation ────────────────────────────────────────────────

# Common aliases across boards
SUBJECT_ALIASES: dict[str, str] = {
    "maths": "Mathematics",
    "math": "Mathematics",
    "mathematics": "Mathematics",
    "english": "English",
    "english language": "English",
    "english literature": "English",
    "eng": "English",
    "physics": "Physics",
    "phy": "Physics",
    "chemistry": "Chemistry",
    "chem": "Chemistry",
    "biology": "Biology",
    "bio": "Biology",
    "computer science": "Computer Science",
    "computers": "Computer Science",
    "cs": "Computer Science",
    "informatics practices": "Informatics Practices",
    "ip": "Informatics Practices",
    "social science": "Social Science",
    "social studies": "Social Science",
    "history": "History",
    "geography": "Geography",
    "economics": "Economics",
    "eco": "Economics",
    "accountancy": "Accountancy",
    "accounts": "Accountancy",
    "business studies": "Business Studies",
    "hindi": "Hindi",
    "kannada": "Kannada",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "marathi": "Marathi",
    "sanskrit": "Sanskrit",
    "second language": "Second Language",
    "third language": "Third Language",
    "physical education": "Physical Education",
    "pe": "Physical Education",
}


def normalise(name: str) -> str:
    """Lowercase, strip punctuation, collapse spaces, then map aliases."""
    cleaned = re.sub(r"[^a-z0-9 ]", "", name.lower().strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return SUBJECT_ALIASES.get(cleaned, cleaned.title())


def subject_similarity(a: str, b: str) -> float:
    """
    Simple token-overlap similarity (0–1).
    Good enough for subject name matching without external deps.
    """
    ta = set(normalise(a).lower().split())
    tb = set(normalise(b).lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def best_match(query: str, candidates: list[str], threshold: float = 0.5) -> Optional[str]:
    """Return the best matching candidate subject name or None."""
    scores = [(c, subject_similarity(query, c)) for c in candidates]
    scores.sort(key=lambda x: x[1], reverse=True)
    if scores and scores[0][1] >= threshold:
        return scores[0][0]
    return None


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class SubjectResult:
    subject_entered: str          # as typed in the form
    subject_matched: Optional[str]  # matched key in extracted JSON
    marks_entered: Optional[float]
    marks_extracted: Optional[float]
    status: str  # "match" | "mismatch" | "not_found" | "grade_only"
    delta: Optional[float] = None  # extracted − entered

    @property
    def is_ok(self) -> bool:
        return self.status == "match"


@dataclass
class ComparisonReport:
    student_name_entered: Optional[str]
    student_name_extracted: Optional[str]
    roll_entered: Optional[str]
    roll_extracted: Optional[str]
    board_extracted: Optional[str]
    exam_year_extracted: Optional[str]
    subject_results: list[SubjectResult] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        if not self.subject_results:
            return "error"
        if all(r.is_ok for r in self.subject_results):
            return "verified"
        mismatches = [r for r in self.subject_results if r.status == "mismatch"]
        not_found  = [r for r in self.subject_results if r.status == "not_found"]
        if mismatches or not_found:
            return "flagged"
        return "warning"  # grade_only subjects only

    @property
    def flagged_subjects(self) -> list[SubjectResult]:
        return [r for r in self.subject_results if not r.is_ok]

    @property
    def match_rate(self) -> float:
        if not self.subject_results:
            return 0.0
        ok = sum(1 for r in self.subject_results if r.is_ok)
        return ok / len(self.subject_results)


# ── Main comparison function ──────────────────────────────────────────────────

def compare(
    form_data: dict,
    extracted: dict,
    tolerance: int = 0,
) -> ComparisonReport:
    """
    form_data = {
        "student_name": str | None,
        "roll_number": str | None,
        "subjects": {"Subject": marks_or_None, ...}
    }
    extracted = full dict from extractor.py
    tolerance = allowed marks difference before flagging (default 0 = exact match)
    """

    report = ComparisonReport(
        student_name_entered=form_data.get("student_name"),
        student_name_extracted=extracted.get("student_name"),
        roll_entered=form_data.get("roll_number"),
        roll_extracted=extracted.get("roll_number"),
        board_extracted=extracted.get("board"),
        exam_year_extracted=extracted.get("exam_year"),
    )

    extracted_subjects: dict = extracted.get("subjects") or {}
    extracted_keys = list(extracted_subjects.keys())

    for subj_entered, marks_entered in (form_data.get("subjects") or {}).items():
        # Try to find a matching subject in extracted data
        matched_key = best_match(subj_entered, extracted_keys)

        if matched_key is None:
            report.subject_results.append(SubjectResult(
                subject_entered=subj_entered,
                subject_matched=None,
                marks_entered=marks_entered,
                marks_extracted=None,
                status="not_found",
            ))
            continue

        marks_extracted = extracted_subjects[matched_key]

        # Grade-only subject (VLM returned null for marks)
        if marks_extracted is None:
            report.subject_results.append(SubjectResult(
                subject_entered=subj_entered,
                subject_matched=matched_key,
                marks_entered=marks_entered,
                marks_extracted=None,
                status="grade_only",
            ))
            continue

        # Both have numeric marks
        try:
            me = float(marks_entered) if marks_entered is not None else None
            mx = float(marks_extracted)
        except (TypeError, ValueError):
            report.subject_results.append(SubjectResult(
                subject_entered=subj_entered,
                subject_matched=matched_key,
                marks_entered=marks_entered,
                marks_extracted=marks_extracted,
                status="not_found",
            ))
            continue

        if me is None:
            status = "not_found"
            delta = None
        else:
            delta = mx - me
            status = "match" if abs(delta) <= tolerance else "mismatch"

        report.subject_results.append(SubjectResult(
            subject_entered=subj_entered,
            subject_matched=matched_key,
            marks_entered=me,
            marks_extracted=mx,
            status=status,
            delta=delta,
        ))

    return report
