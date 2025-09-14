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

# ---------- lazy model access (faster cold starts, easier testing) ----------
@lru_cache(maxsize=1)
def _get_semantic_model() -> SentenceTransformer:
    return SentenceTransformer('all-MiniLM-L6-v2')

@lru_cache(maxsize=1)
def _get_kw_model() -> KeyBERT:
    # Reuse the same embedding model inside KeyBERT
    return KeyBERT(model=_get_semantic_model())

# ---------- your helpers (unchanged) ----------
def get_type_from_tag(tag: str) -> str:
    return TAG_TO_TYPE_MAP.get(tag, 'Other')

def find_semantic_matches(data: Dict[str, Any], analysis_type: str, top_n: int = 3) -> List[str]:
    concept_text = SEMANTIC_CONCEPTS.get(analysis_type)
    if not concept_text:
        raise ValueError(f"Analysis type '{analysis_type}' not found in SEMANTIC_CONCEPTS.")

    MODEL = _get_semantic_model()
    concept_embedding = MODEL.encode([concept_text])

    all_sentences: List[str] = []
    for msg in data.get('messages', []):
        content = msg.get('content', '') or ''
        if not content:
            continue
        # keep simple; split on sentence enders
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
    kw_model = _get_kw_model()
    primary_tag = data.get('tag', '') or ''
    description = data.get('description', '') or ''
    text = f"{primary_tag}. {description}".strip(". ")
    if not text:
        return []
    keywords = kw_model.extract_keywords(
        text,
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

def _to_data_for_semantics(messages: List[Dict[str, Any]], tag: str = "", description: str = "") -> Dict[str, Any]:
    """Adapt your ChatMessage list to the shape expected by the extractors."""
    return {
        "messages": [{"content": m.get("content", "")} for m in messages],
        "tag": tag,
        "description": description,
    }

def enrich_conversation_with_semantics(
    messages: List[Dict[str, Any]],
    conversation_tag: str,
    conversation_description: str,
    before_code: Optional[str] = None,
    after_code: Optional[str] = None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    Runs all non-LLM semantic enrichments and returns a bundle you can attach
    to your ConversationSummary or logs.
    """
    data = _to_data_for_semantics(messages, conversation_tag, conversation_description)

    feature_sentences = extract_functions(data, concept="feature_development")
    bugfix_sentences = extract_bug_fixes(data, concept="bug_fix")
    keyphrases = extract_tags(data, top_n=6)

    conv_type = get_type_from_tag(conversation_tag)
    code_block = format_code_changes(before_code, after_code)

    return {
        "conventional_type": conv_type,         # e.g., 'feat' | 'fix' | 'chore' | 'security' | 'Other'
        "feature_sentences": feature_sentences, # top N semantically similar to "feature development"
        "bugfix_sentences": bugfix_sentences,   # top N semantically similar to "bug fix"
        "keywords": keyphrases,                 # keyphrases for indexing/search
        "formatted_code_changes": code_block,   # pretty-printed before/after block (if provided)
    }
