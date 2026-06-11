"""
utils/extractor.py
Handles marksheet image → structured JSON via Gemini Vision.
"""

import os
import json
import re
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import google.generativeai as genai


SYSTEM_PROMPT = """You are an expert at reading academic marksheets and certificates from Indian boards (CBSE, ICSE, Karnataka SSLC/PUC, Maharashtra SSC/HSC, TN SSLC/HSC, and all other state boards).

Extract the following from the marksheet image and return ONLY valid JSON, no explanation, no markdown, no backticks:

{
  "student_name": "full name as printed",
  "roll_number": "roll/register/seat number",
  "board": "board name",
  "exam_year": "year of exam",
  "class": "10 or 12",
  "subjects": {
    "Subject Name": marks_as_integer_or_float
  },
  "total_marks": total_if_printed_else_null,
  "percentage": percentage_if_printed_else_null,
  "result": "PASS or FAIL or null"
}

Rules:
- Use ONLY final/theory marks — NOT internal assessment, practical, or grace marks.
- If a subject has only a grade and no marks, set its value to null.
- Auto-correct subject name spelling (e.g. "Matematics" → "Mathematics").
- Translate non-English subject names to their standard English equivalents.
- If a field is not found, set it to null.
- Return nothing except the JSON object.
"""


def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)


def pdf_to_pil_image(pdf_bytes: bytes) -> Image.Image:
    """Convert first page of a PDF to a PIL Image."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    # High DPI for better OCR accuracy
    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def pil_to_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def extract_from_image(img: Image.Image, api_key: str) -> dict:
    """Send image to Gemini Vision and return parsed JSON."""
    configure_gemini(api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    img_bytes = pil_to_bytes(img)
    image_part = {"mime_type": "image/png", "data": img_bytes}

    response = model.generate_content([SYSTEM_PROMPT, image_part])
    raw = response.text.strip()

    # Strip accidental markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()

    parsed = json.loads(raw)

    # Normalise subject names: strip trailing punctuation, title-case
    if "subjects" in parsed and parsed["subjects"]:
        clean = {}
        for k, v in parsed["subjects"].items():
            key = k.strip(" .:;,").title()
            clean[key] = v
        parsed["subjects"] = clean

    return parsed


def extract_from_uploaded_file(uploaded_file, api_key: str) -> tuple[dict, Image.Image]:
    """
    Accepts a Streamlit UploadedFile (PDF or image).
    Returns (extracted_dict, preview_pil_image).
    """
    file_bytes = uploaded_file.read()

    if uploaded_file.type == "application/pdf":
        img = pdf_to_pil_image(file_bytes)
    else:
        img = Image.open(BytesIO(file_bytes)).convert("RGB")

    result = extract_from_image(img, api_key)
    return result, img
