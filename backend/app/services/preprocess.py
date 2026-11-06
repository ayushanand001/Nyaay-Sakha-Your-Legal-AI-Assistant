"""
Case-text cleanup copied from the CJPE training notebook.

The outcome model was trained on normalized judgment text with the court's
own analysis removed. Prediction uses that same model input.
"""

import re

PARA_MARKER = re.compile(r"^\s*(?:\[\d+(?:\.\d+)*\]|\(\d+\))\s*")
HEADING_LINE = re.compile(
    r"^\s*(?:JUDGMENT|JUDGEMENTS?|ORDER|OPERATIVE ORDER|FINAL ORDER|"
    r"CONCLUSION|RESULT|APPEARANCES|REPORTABLE|NON-REPORTABLE)\s*$",
    re.IGNORECASE,
)
SIGNATURE_LINE = re.compile(
    r"^\s*(?:Digitally\s+signed\s+by\b.*|"
    r"Date:\s*\d{4}[.-]\d{2}[.-]\d{2}.*|"
    r"Reason:\s*.*|"
    r"\d{1,2}:\d{2}:\d{2}\s+IST)\s*$",
    re.IGNORECASE,
)
ANALYSIS_START_PATTERNS = [
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?Heard\s+(?:learned|Ld\.?|the)\s+",
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?We\s+have\s+heard\b",
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?Having\s+heard\b",
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?We\s+have\s+considered\b",
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?The\s+question\s+(?:which|that)\s+(?:arises|falls)",
    r"^\s*(?:\[\d+(?:\.\d+)*\]\s*)?The\s+short\s+question\b",
]
ANALYSIS_START_RE = re.compile(
    "|".join(f"(?:{pattern})" for pattern in ANALYSIS_START_PATTERNS),
    re.IGNORECASE | re.MULTILINE,
)
MIN_MODEL_CHARS = 500


def prepare_case_text(text):
    cleaned = normalize_text(text or "")
    analysis_start, _method = locate_analysis_start(cleaned)
    model_text, status = remove_court_analysis(cleaned, analysis_start)
    return model_text, status


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u00ad", "")
    text = re.sub(r"[\u200b\ufeff]", "", text)
    text = re.sub(r"\bSignature\s+Not\s+Verified\b", "", text, flags=re.IGNORECASE)

    output_paragraphs = []
    current_lines = []

    def flush():
        nonlocal current_lines
        if current_lines:
            paragraph = " ".join(line.strip() for line in current_lines if line.strip())
            paragraph = re.sub(r"[ \t]+", " ", paragraph).strip()
            if paragraph:
                output_paragraphs.append(paragraph)
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"\d{1,4}", line):
            continue
        if SIGNATURE_LINE.match(line):
            continue
        if re.fullmatch(r"[A-Z][A-Za-z .-]{1,40}", line) and line.lower() in {
            "natarajan",
            "digitally signed",
        }:
            continue
        if PARA_MARKER.match(line) or HEADING_LINE.match(line):
            flush()
        current_lines.append(line)

    flush()
    return "\n\n".join(output_paragraphs).strip()


def locate_analysis_start(text):
    match = ANALYSIS_START_RE.search(text)
    if not match:
        return None, "analysis_start_not_found"
    return match.start(), "analysis_start_phrase"


def remove_court_analysis(cleaned_text, analysis_start):
    if analysis_start is None:
        return "", "analysis_removal_not_confirmed"
    model_text = cleaned_text[:analysis_start].strip()
    if len(model_text) < MIN_MODEL_CHARS:
        return "", "analysis_removal_too_short"
    return model_text, "truncated_before_court_analysis"
