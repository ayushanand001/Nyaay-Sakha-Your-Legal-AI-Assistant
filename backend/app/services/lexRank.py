"""
LexRank from scratch: TF-IDF -> cosine similarity graph -> power iteration (PageRank-style).
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def strip_boilerplate(text: str, header_pattern: str = None) -> str:
    """
    Remove repeated page header/footer boilerplate that court PDF-to-text
    extraction commonly injects mid-paragraph, e.g.:
        "Patna High Court CR. WJC No.2913 of 2025 dt.11-09-2026"
    Left in, this exact repeated string appears in many sentences and makes
    them look artificially similar to each other in the TF-IDF/cosine step,
    and also breaks sentence splitting when it lands mid-sentence.

    Pass a custom regex via header_pattern for other courts' header formats.
    The default pattern targets the "<Court Name> High Court CR. <case type>
    No.<number> of <year> dt.<date>" style used in the Patna HC PDF exports.
    """
    if header_pattern is None:
        header_pattern = r'\b[A-Za-z]+\s+High\s+Court\s+CR\.?\s+\w+\s+No\.\s*\d+\s+of\s+\d{4}\s+dt\.[\d\-]+\b'
    return re.sub(header_pattern, ' ', text, flags=re.IGNORECASE)


def strip_paragraph_numbers(text: str) -> str:
    """
    Remove leading/inline numbered-paragraph markers common in judgment text,
    e.g. "26. In the present case..." or "...registered. 26. In the present".
    These are document structure markers, not sentence-ending abbreviations,
    but they look identical to "number + period" and would otherwise get
    glued onto the preceding sentence by the splitter.
    """
    # A digit-only "sentence" like "26." sitting between two real sentences
    return re.sub(r'(?<=[.!?])\s+\d{1,3}\.\s+', ' ', text)


def split_sentences(text: str, strip_headers: bool = False,
                     header_pattern: str = None) -> list[str]:
    """
    Dependency-free sentence splitter (no NLTK download required).
    Handles common abbreviations reasonably well and collapses whitespace/newlines
    so multi-line paragraphs don't get split mid-sentence.

    Note: splits on '.', '!', '?' followed by whitespace, regardless of the case
    of the next letter -- this also correctly handles lowercased/normalized text
    (e.g. legal corpora that have been lowercased), where a capital-letter check
    would otherwise merge every sentence into one.

    strip_headers: set True for court judgment PDFs that have repeated page
    header/footer text embedded mid-paragraph (see strip_boilerplate()).
    Also strips numbered-paragraph markers ("26.", "38.") which cause the
    same kind of false sentence break.
    """
    normalized = re.sub(r'\s+', ' ', text.strip())

    if strip_headers:
        normalized = strip_boilerplate(normalized, header_pattern)
        normalized = strip_paragraph_numbers(normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Common abbreviations that shouldn't be treated as sentence boundaries
    abbreviations = [
        "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.",
        "vs.", "Vs.", "VS.", "v.", "etc.", "e.g.", "i.e.", "U.S.", "U.K.",
        "Fig.", "No.", "Ors.", "Anr.", "J.", "C.J.", "Art.", "Cl.",
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.",
        "etc.", "no.", "ors.", "anr.",
    ]
    placeholder = "<!DOT!>"
    for abbr in abbreviations:
        normalized = normalized.replace(abbr, abbr.replace(".", placeholder))

    # Split on '.', '!', '?' followed by whitespace + any letter (or end of string)
    # -- no longer requires the next letter to be uppercase
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Za-z]|$)', normalized)

    # Restore the protected periods and clean up
    sentences = [s.replace(placeholder, ".").strip() for s in raw_sentences if s.strip()]
    return sentences


def strip_citations(text: str) -> str:
    """
    Remove/normalize legal citation patterns before vectorization, so they don't
    create spurious similarity between sentences that just happen to cite
    similar-looking case numbers.

    This targets patterns common in Indian case law text (the kind of corpus
    this script was tested against), such as:
        "1993 1 scc 435 1993 indlaw sc 1325"
        "2005 2 scc 334 2005 indlaw sc 6"
        "air 1965 sc 1585 1964 indlaw sc 353"
        "section 257"  /  "sections 247 and 249"

    Adjust the patterns below if your corpus uses different citation formats
    (e.g. US Reporter citations, neutral citations, etc.).
    """
    cleaned = text

    # Reporter citations with parens/commas: e.g. "(1966) 1 SCR 709", "(2023) 9 SCC 587"
    cleaned = re.sub(
        r'\(\d{4}\)\s*\d+\s+(scc|scr)\s+\d+\b',
        ' ', cleaned, flags=re.IGNORECASE
    )

    # "SCC OnLine" citations: e.g. "2026 SCC OnLine 1726", "1965 SCC OnLine SC 9"
    cleaned = re.sub(
        r'\b\d{4}\s+scc\s+online(\s+sc)?\s+\d+\b',
        ' ', cleaned, flags=re.IGNORECASE
    )

    # Reporter citations: e.g. "1993 1 scc 435", "2 scc 334", "air 1965 sc 1585"
    cleaned = re.sub(
        r'\b(air\s+)?\d{4}\s+\d+\s+(scc|scr)\s+\d+\b',
        ' ', cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r'\b\d+\s+(scc|scr)\s+\d+\b',
        ' ', cleaned, flags=re.IGNORECASE
    )

    # "indlaw sc 1325", "indlaw sc 6" style citations
    cleaned = re.sub(r'\bindlaw\s+sc\s+\d+\b', ' ', cleaned, flags=re.IGNORECASE)

    # Bare "air 1965 sc 1585" without the leading reporter pattern above
    cleaned = re.sub(r'\bair\s+\d{4}\s+sc\s+\d+\b', ' ', cleaned, flags=re.IGNORECASE)

    # Section/sub-section references: "section 257", "sections 247 and 249", "section 8i"
    cleaned = re.sub(
        r'\bsections?\s+\d+[a-z]?(\s*(and|,)\s*\d+[a-z]?)*\b',
        ' ', cleaned, flags=re.IGNORECASE
    )

    # NOTE: Case-name stripping ("X vs. Y and Others") was tried and removed --
    # it's unreliable via regex because real citations vary too much ("and
    # Another", "and Ors.", "Alias X", lowercase conjunctions mid-name) for a
    # pattern to bound consistently. Reliable case-name detection needs NER
    # (e.g. spaCy), not regex. The citation-number patterns above are the
    # reliable part of this cleanup.

    # Survey/mutation/entry numbers: "survey nos 351 and 1182", "mutation entry no 1836"
    cleaned = re.sub(
        r'\b(survey|mutation entry|cts|rts)\s+nos?\.?\s+[\d\s,and]+\b',
        ' ', cleaned, flags=re.IGNORECASE
    )

    # Collapse whitespace left behind by the removals
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def build_similarity_matrix(sentences: list[str], clean_citations: bool = False) -> np.ndarray:
    """
    TF-IDF vectorize sentences, then compute pairwise cosine similarity.

    clean_citations: if True, runs strip_citations() on a COPY of the sentences
    used only for vectorization -- the original sentence text (returned in the
    summary) is untouched. Use this for legal/citation-heavy corpora.
    """
    vectorize_input = [strip_citations(s) for s in sentences] if clean_citations else sentences

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(vectorize_input)     # shape: (N, vocab_size)
    sim_matrix = cosine_similarity(tfidf_matrix)                # shape: (N, N)
    np.fill_diagonal(sim_matrix, 0)                             # no self-loops
    return sim_matrix


def power_iteration(sim_matrix: np.ndarray, damping: float = 0.85,
                     max_iter: int = 100, tol: float = 1e-4) -> np.ndarray:
    """
    Solve for the LexRank scores via the power method.
    This is the PageRank recurrence applied to the sentence similarity graph.
    """
    n = sim_matrix.shape[0]

    # Row-normalize the similarity matrix so each row sums to 1 (transition probabilities)
    row_sums = sim_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # avoid divide-by-zero for isolated sentences
    transition_matrix = sim_matrix / row_sums

    scores = np.ones(n) / n  # uniform initialization

    for iteration in range(max_iter):
        new_scores = (damping / n) + (1 - damping) * transition_matrix.T.dot(scores)
        # ^ note: (damping/n) acts as the random-jump term; (1-damping) weights the graph walk
        #   this mirrors the LexRank formula: d/N term + (1-d) * weighted neighbor sum

        diff = np.abs(new_scores - scores).sum()
        scores = new_scores
        if diff < tol:
            break

    return scores


def lexrank_summarize(text: str, num_sentences: int = 3, damping: float = 0.85,
                       clean_citations: bool = False, strip_headers: bool = False,
                       header_pattern: str = None) -> list[str]:
    """
    Full pipeline: text -> sentences -> similarity graph -> scores -> top-K summary.

    clean_citations: set True for legal/citation-heavy text (case numbers, section
    references, survey/mutation numbers) so they don't distort sentence similarity.
    strip_headers: set True for court judgment PDFs with repeated page header/
    footer boilerplate embedded mid-paragraph (see strip_boilerplate()).
    The returned summary sentences are always the original, unmodified text.
    """
    sentences = split_sentences(text, strip_headers=strip_headers, header_pattern=header_pattern)
    if len(sentences) <= num_sentences:
        return sentences

    sim_matrix = build_similarity_matrix(sentences, clean_citations=clean_citations)
    scores = power_iteration(sim_matrix, damping=damping)

    # Rank sentence indices by score, take top-K, then restore original order
    ranked_idx = np.argsort(scores)[::-1][:num_sentences]
    ranked_idx_sorted_by_position = sorted(ranked_idx)

    summary = [sentences[i] for i in ranked_idx_sorted_by_position]
    return summary


if __name__ == "__main__":
    sample_text = """
    The Supreme Court delivered a landmark judgment on data privacy today. The ruling establishes
    that individuals have a fundamental right to privacy under the constitution. This decision
    overturns several previous rulings that did not recognize privacy as a fundamental right.
    Legal experts believe this will have far-reaching implications for data protection laws.
    The judgment specifically addresses the collection of biometric data by government agencies.
    Privacy advocates have welcomed the ruling as a major victory for civil liberties.
    However, some government officials expressed concern that the ruling could complicate
    national security operations. The court clarified that privacy is not an absolute right
    and can be reasonably restricted by law. This balancing test will now be applied in future
    cases involving surveillance and data collection. The judgment is expected to influence
    pending legislation on data protection currently before parliament.
    """

    summary = lexrank_summarize(sample_text, num_sentences=3)
    print("=== LexRank Summary ===")
    for i, sent in enumerate(summary, 1):
        print(f"{i}. {sent}")