# DigiCert — Marksheet Verification System

Automates the first pass of marksheet verification for college admissions.  
Accepts marksheets from any Indian board in any language, extracts structured data via Gemini Vision, and compares against applicant-entered marks.

---

## File structure

```
digicert/
│
├── app.py                  # Streamlit entry point, global styles, nav routing
│
├── pages/
│   ├── verify.py           # Main flow: form entry → upload → extract → compare → result
│   ├── results.py          # College admin: list + drill-down of all past records
│   └── settings.py         # API key config, tolerance defaults, about
│
├── utils/
│   ├── extractor.py        # PDF/image → Gemini Vision → structured JSON
│   ├── comparator.py       # Form JSON vs extracted JSON → diff report
│   └── storage.py          # Save/load verification records (local JSON files)
│
├── data/
│   └── records/            # Auto-created. One .json file per verification run.
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

```bash
# 1. Clone / copy the project folder
cd digicert

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Gemini API key
cp .env.example .env
# Edit .env and paste your key from https://aistudio.google.com/app/apikey

# 5. Run
streamlit run app.py
```

Alternatively, paste your API key directly in the **Settings** tab — no `.env` needed.

---

## How verification works

1. **Form entry** — applicant enters subjects and claimed marks  
2. **Upload** — PDF or image of the marksheet (any board, any language)  
3. **Extraction** — Gemini 2.0 Flash Vision reads the marksheet and returns structured JSON  
   - Only final/theory marks extracted (not internal, practical, or grace marks)  
   - Subject names auto-corrected and translated to English  
4. **Comparison** — entered vs extracted marks matched with fuzzy subject name matching  
   - Tolerance: configurable (0 = exact, up to 5 marks leeway)  
   - Grade-only subjects flagged separately (no numeric marks available)  
5. **Result** — Verified / Flagged / Warning  
   - Flagged applications queued for manual review  
   - All results saved to `data/records/` for audit trail  

---

## Supported boards

All Indian boards including CBSE, ICSE, Karnataka SSLC/PUC, Maharashtra SSC/HSC,  
Tamil Nadu SSLC/HSC, AP/Telangana Boards, Kerala, UP Board, Rajasthan, and more.  
Regional language marksheets supported via Gemini's multilingual capability.

---

## Roadmap

- [ ] DigiLocker direct pull for CBSE + major state boards  
- [ ] Multi-page marksheet support (currently page 1 only)  
- [ ] Confidence score per extracted field  
- [ ] CSV export of records  
- [ ] College admin role with approve/reject actions  
- [ ] Swap VLM backend (Claude Vision, GPT-4o)  
