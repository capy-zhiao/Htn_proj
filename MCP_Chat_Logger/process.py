from typing import List, Dict, Any, Optional
from functools import lru_cache
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT

TAG_TO_TYPE_MAP = {
    'function added': 'feat',
    'function modify': 'feat',
    'bug fixed': 'fix',
    'vulnerability patched': 'security',
    'question': 'chore',
    'discussion': 'chore',
    'other': 'chore'
}

SEMANTIC_CONCEPTS = {
    "feature_development": "A developer is creating, implementing, refactoring, or adding a new function/method to the code.",
    "bug_fix": "A developer is fixing, patching, or resolving a bug, error, issue, or problem in the software.",
}

@lru_cache(maxsize=1)
def get_semantic_model() -> SentenceTransformer:
    return SentenceTransformer('all-MiniLM-L6-v2')

@lru_cache(maxsize=1)
def get_kw_model() -> KeyBERT:
    return KeyBERT(model=get_semantic_model())

def get_type_from_tag(tag: str) -> str:
    return TAG_TO_TYPE_MAP.get(tag, 'Other')

def find_semantic_matches(data: Dict[str, Any], analysis_type: str, top_n: int = 3) -> List[str]:
    concept_text = SEMANTIC_CONCEPTS.get(analysis_type)
    if not concept_text:
        raise ValueError(f"Analysis type '{analysis_type}' not found in SEMANTIC_CONCEPTS.")

    MODEL = get_semantic_model()
    concept_embedding = MODEL.encode([concept_text])

    all_sentences: List[str] = []
    for msg in data.get('messages', []):
        content = msg.get('content', '') or ''
        if not content:
            continue
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', content) if s.strip()]
        all_sentences.extend(sentences)

    if not all_sentences:
        return []

    sentence_embeddings = MODEL.encode(all_sentences)
    sims = cosine_similarity(concept_embedding, sentence_embeddings)[0]
    ranked = sorted(zip(all_sentences, sims), key=lambda x: x[1], reverse=True)
    return [s for s, _ in ranked[:top_n]]

def extract_functions(data: Dict[str, Any], concept: str = "feature_development") -> List[str]:
    raw_sentences = find_semantic_matches(data, concept, top_n=10)
    return raw_sentences

def extract_bug_fixes(data: Dict[str, Any], concept: str = "bug_fix") -> List[str]:
    raw_sentences = find_semantic_matches(data, concept, top_n=10)
    return raw_sentences

def extract_tags(data: Dict[str, Any], top_n: int = 6) -> List[str]:
    kw_model = get_kw_model()
    primary_tag = data.get('tag', '')
    if not primary_tag:
        return []
    keywords = kw_model.extract_keywords(
        text=primary_tag,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        use_mmr=True,
        diversity=0.4,
        top_n=top_n,
    )
    return [kw for kw, _ in keywords]

def format_code_changes(before_code: Optional[str], after_code: Optional[str]) -> str:
    if not before_code and not after_code:
        return '// No code changes detected'
    parts = []
    if before_code:
        parts.append(f"// Before:\n{before_code}")
    if after_code:
        parts.append(f"// After:\n{after_code}")
    return '\n\n'.join(parts)


# ---- Local enrichment using process.py ----
def _attach_enrichment(base: Dict[str, Any]) -> Dict[str, Any]:
    msg_type = base.get("type", "unknown")
    tag_for_helpers = TAG_TO_TYPE_MAP.get(msg_type, "other")
    conventional = get_type_from_tag(tag_for_helpers)

    data_for_helpers = {
        "messages": [{"content": base.get("content", "")}],
        "tag": tag_for_helpers,
    }

    try:
        feature_sentences = extract_functions(data_for_helpers, concept="feature_development")
    except Exception:
        feature_sentences = []
    try:
        bugfix_sentences = extract_bug_fixes(data_for_helpers, concept="bug_fix")
    except Exception:
        bugfix_sentences = []
    try:
        keywords = extract_tags(data_for_helpers, top_n=6)
    except Exception:
        keywords = []

    try:
        formatted_cc = (
            format_code_changes(base.get("before_code"), base.get("after_code"))
            if (base.get("before_code") or base.get("after_code"))
            else (format_code_changes(None, base.get("code_changes")) if base.get("code_changes") else "// No code changes detected")
        )
    except Exception:
        formatted_cc = "// No code changes detected"

    base["enrichment"] = {
        "conventional_type": conventional,
        "feature_sentences": feature_sentences,
        "bugfix_sentences": bugfix_sentences,
        "keywords": keywords,
        "formatted_code_changes": formatted_cc,
    }
    return base

def normalize_llm_type(v: Any) -> str:
    t = str(v or "").strip().lower().replace("_", "-")
    if t in TAG_TO_TYPE_MAP.keys():
        return t
    t = TAG_TO_TYPE_MAP.get(t, t)
    return t if t in TAG_TO_TYPE_MAP else "discussion"