"""
Enhanced Legal Document Summarizer for Nyaay Sakha.
Combines Legal-Domain Salience Weighting + LexRank (Graph-based PageRank) + Maximal Marginal Relevance (MMR).
"""

import math
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LEGAL_KEYWORDS = {
    "relief": [
        "bail", "anticipatory", "appeal", "petition", "quashing", "writ",
        "prayer", "seeks", "application", "revision", "injunction", "stay",
    ],
    "facts": [
        "allegation", "alleged", "prosecution", "informant", "accused", "fir",
        "incident", "dispute", "occurrence", "charge-sheet", "chargesheet",
        "custody", "arrest", "investigation", "recovery", "weapon", "injured",
    ],
    "statute": [
        "section", "sections", "ipc", "crpc", "cpc", "act", "code", "constitution",
        "article", "penal", "criminal", "civil", "offence", "offences",
    ],
    "contentions": [
        "submits", "submitted", "contended", "contention", "argued", "argument",
        "learned counsel", "opposes", "opposed", "pleaded", "plea", "averred",
    ],
    "findings": [
        "considered", "view", "opinion", "held", "finding", "directed", "ordered",
        "granted", "rejected", "dismissed", "allowed", "disposed", "released",
        "satisfied", "manifest", "manifests", "liberty", "reasons",
    ],
}

NOISE_PATTERNS = [
    r"^(?:IN THE HIGH COURT|COURT OF|SUPREME COURT|DISTRICT COURT)\b",
    r"^(?:CRIMINAL|CIVIL|WRIT|SPECIAL LEAVE)\s+(?:MISC|APPEAL|PETITION|APPLICATION)\b",
    r"^(?:Arising Out of|Police Station|District:)\b",
    r"^(?:Appearance|CORAM|ORAL ORDER|FINAL ORDER|JUDGMENT|ORDER)\s*[:.]?",
    r"^(?:For the Petitioner|For the State|For the Opposite Party|Advocate)\b",
    r"^(?:Digitally signed by|Signature Not Verified|Date:\s*\d{4})\b",
    r"^(?:Page \d+|\(\d+\)|\d{1,4}\.?)\s*$",
    r"^[A-Z\s,.-]+/\-?\s*$",  # e.g. "Kundan/-"
    r"^\([A-Za-z\s.,-]+\)\s*$",  # e.g. "(Satyavrat Verma, J)"
]
NOISE_RE = re.compile("|".join(f"(?:{p})" for p in NOISE_PATTERNS), re.IGNORECASE)


def is_informative_sentence(s: str) -> bool:
    """Filter out administrative headers, appearance rosters, and signature stamps."""
    words = s.split()
    if len(words) < 6:
        return False
    if NOISE_RE.search(s):
        return False
    if re.search(r"\b(Versus|Petitioner/s|Opposite Party/s|Appearance :|Advocate For)\b", s, re.IGNORECASE):
        return False
    # Must contain at least one ASCII word with length > 2
    if not any(len(w) >= 3 and w.isalpha() for w in words):
        return False
    return True


def strip_citations(text: str) -> str:
    """Remove legal citation numbers so sentences don't gain false similarity."""
    cleaned = text
    cleaned = re.sub(r"\(\d{4}\)\s*\d+\s+(?:scc|scr)\s+\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{4}\s+scc\s+online(?:\s+sc)?\s+\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:air\s+)?\d{4}\s+\d+\s+(?:scc|scr)\s+\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d+\s+(?:scc|scr)\s+\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bindlaw\s+sc\s+\d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bsections?\s+\d+[a-z]?(?:\s*(?:and|,)\s*\d+[a-z]?)*\b", " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def split_sentences(text: str) -> list[str]:
    """Robust sentence segmentation preserving legal abbreviations."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    abbreviations = [
        "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.",
        "vs.", "Vs.", "VS.", "v.", "etc.", "e.g.", "i.e.", "U.S.", "U.K.",
        "Fig.", "No.", "Nos.", "Ors.", "Anr.", "J.", "C.J.", "Art.", "Cl.",
        "P.S.", "Cr.P.C.", "C.P.C.", "I.P.C.", "S.C.R.", "S.C.C.", "A.I.R.",
        "dt.", "para.", "paras.", "sec.", "secs.",
    ]
    placeholder = "<!DOT!>"
    for abbr in abbreviations:
        normalized = normalized.replace(abbr, abbr.replace(".", placeholder))

    # Split on period, exclamation, or question mark followed by whitespace
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Za-z0-9]|$)", normalized)
    sentences = [
        s.replace(placeholder, ".").strip()
        for s in raw_sentences
        if s.strip()
    ]
    return sentences


def compute_legal_salience(sentence: str, position_idx: int, total_sents: int) -> float:
    """Compute prior semantic importance based on legal domain signals and document flow."""
    s_lower = sentence.lower()
    score = 1.0

    # Domain keyword coverage
    for category, kw_list in LEGAL_KEYWORDS.items():
        if any(kw in s_lower for kw in kw_list):
            if category == "relief":
                score += 0.5  # Core prayer/relief sought is vital
            elif category == "findings":
                score += 0.45  # Court's conclusions
            elif category == "facts":
                score += 0.35  # Essential background
            else:
                score += 0.25

    # Positional bonus: Beginning (case setup) and Ending (adjudication) carry higher weight
    pos_ratio = position_idx / max(total_sents, 1)
    if pos_ratio <= 0.2:
        score += 0.35
    elif pos_ratio >= 0.8:
        score += 0.3

    return score


def extract_key_points(selected_sentences: list[str]) -> list[str]:
    """Categorize chosen summary sentences into structured legal takeaways."""
    key_points = []
    for s in selected_sentences:
        sl = s.lower()
        if any(k in sl for k in ["considered", "is of the view", "held that", "directed that", "hereby ordered", "ordered that", "finding of", "satisfied that"]):
            tag = "[Judicial Consideration]"
        elif any(k in sl for k in ["seeks regular bail", "seeks anticipatory bail", "prayed for", "prayer for", "prayer of", "seeks bail", "quashing of", "appeal is directed", "prays for"]):
            tag = "[Case Prayer & Relief]"
        elif any(k in sl for k in ["submits that", "submitted that", "learned counsel for", "opposes the", "opposed the", "contended that", "argued that"]):
            tag = "[Contentions & Submissions]"
        elif any(k in sl for k in ["prosecution alleges", "incident", "informant", "custody for", "charge-sheet", "chargesheet", "dispute", "allegation"]):
            tag = "[Background & Allegations]"
        else:
            tag = "[Key Record]"
        key_points.append(f"{tag} {s}")
    return key_points


def enhanced_lexrank_summarize(
    text: str,
    num_sentences: int = 5,
    damping: float = 0.85,
    redundancy_penalty: float = 0.35,
) -> dict:
    """
    Enhanced Legal Extractive Summarizer:
    1. Preprocesses and filters out procedural noise.
    2. Builds n-gram TF-IDF similarity graph.
    3. Runs Biased PageRank with legal domain priors.
    4. Selects sentences via Maximal Marginal Relevance (MMR) for maximum diversity.
    5. Formats both narrative summary and structured key takeaways.
    """
    all_sentences = split_sentences(text)
    if not all_sentences:
        return {
            "summary": None,
            "sentences": [],
            "key_points": [],
            "reduction_pct": 0,
            "word_count": 0,
        }

    # Filter informative sentences while remembering original indices
    valid_sentences = [
        (idx, s) for idx, s in enumerate(all_sentences)
        if is_informative_sentence(s)
    ]

    # If filtering leaves too few sentences, relax filtering
    if len(valid_sentences) <= num_sentences:
        valid_sentences = list(enumerate(all_sentences))

    num_candidates = len(valid_sentences)
    if num_candidates <= num_sentences:
        chosen = [s for _, s in valid_sentences]
        summary_text = " ".join(chosen)
        orig_words = len(text.split())
        sum_words = len(summary_text.split())
        red_pct = max(0, round((1.0 - (sum_words / max(orig_words, 1))) * 100))
        return {
            "summary": summary_text,
            "sentences": chosen,
            "key_points": extract_key_points(chosen),
            "reduction_pct": red_pct,
            "word_count": sum_words,
        }

    candidate_texts = [s for _, s in valid_sentences]

    # Cleaned text for vectorization
    vectorize_corpus = [strip_citations(s) for s in candidate_texts]

    # TF-IDF matrix (unigrams + bigrams for legal phrases)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=15000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(vectorize_corpus)
    sim_matrix = cosine_similarity(tfidf_matrix)
    np.fill_diagonal(sim_matrix, 0.0)
    sim_matrix[sim_matrix < 0.06] = 0.0  # Prune negligible edges

    # Prior Legal Salience Vector (Personalized PageRank)
    salience_weights = np.array([
        compute_legal_salience(s, orig_idx, len(all_sentences))
        for orig_idx, s in valid_sentences
    ])
    p_vector = salience_weights / salience_weights.sum()

    # Graph walk transition probabilities
    row_sums = sim_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    transition_matrix = sim_matrix / row_sums

    # Power Iteration with personalization
    scores = np.ones(num_candidates) / num_candidates
    for _ in range(80):
        new_scores = (1 - damping) * p_vector + damping * transition_matrix.T.dot(scores)
        if np.abs(new_scores - scores).sum() < 1e-4:
            break
        scores = new_scores

    # Maximal Marginal Relevance (MMR) for diverse, non-redundant coverage
    selected_indices = []
    lambda_param = 1.0 - redundancy_penalty

    # Ensure the first primary substantive relief/prayer sentence is considered
    for _ in range(min(num_sentences, num_candidates)):
        best_idx = None
        best_score = -float("inf")

        for i in range(num_candidates):
            if i in selected_indices:
                continue

            max_sim_to_selected = (
                max([sim_matrix[i, j] for j in selected_indices])
                if selected_indices else 0.0
            )

            # MMR formula
            mmr_score = lambda_param * scores[i] - (1 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        if best_idx is not None:
            selected_indices.append(best_idx)

    # Sort selected sentences chronologically by original appearance in the case
    selected_indices.sort(key=lambda idx: valid_sentences[idx][0])
    chosen_sentences = [candidate_texts[idx] for idx in selected_indices]

    summary_paragraph = " ".join(chosen_sentences)
    orig_word_count = len(text.split())
    summary_word_count = len(summary_paragraph.split())
    reduction_pct = max(0, round((1.0 - (summary_word_count / max(orig_word_count, 1))) * 100))

    return {
        "summary": summary_paragraph,
        "sentences": chosen_sentences,
        "key_points": extract_key_points(chosen_sentences),
        "reduction_pct": reduction_pct,
        "word_count": summary_word_count,
    }


def lexrank_summarize(
    text: str,
    num_sentences: int = 5,
    clean_citations: bool = True,
    strip_headers: bool = True,
    header_pattern: str = None,
) -> list[str]:
    """Compatibility wrapper returning sentences list."""
    res = enhanced_lexrank_summarize(text, num_sentences=num_sentences)
    return res["sentences"]
