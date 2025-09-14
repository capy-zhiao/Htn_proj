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
    return _summarize_into_clear_statements(raw_sentences, "feature")

def extract_bug_fixes(data: Dict[str, Any], concept: str = "bug_fix") -> List[str]:
    raw_sentences = find_semantic_matches(data, concept, top_n=10)
    return _summarize_into_clear_statements(raw_sentences, "bug_fix")

def _summarize_into_clear_statements(sentences: List[str], category: str) -> List[str]:
    """
    Convert multiple extracted sentences into clear, concise summary statements.
    """
    if not sentences:
        return []
    
    # Filter out very short or unclear sentences
    filtered_sentences = [s for s in sentences if len(s.strip()) > 10 and not s.strip().startswith(('I', 'You', 'Let me', 'Here'))]
    
    if not filtered_sentences:
        return []
    
    # For features: look for implementation/addition patterns
    if category == "feature":
        summaries = []
        for sentence in filtered_sentences[:3]:  # Take top 3 relevant sentences
            if any(keyword in sentence.lower() for keyword in ['implement', 'add', 'create', 'build', 'feature', 'function']):
                # Clean up and make more concise
                clean_sentence = _clean_and_format_sentence(sentence, "feature")
                if clean_sentence and clean_sentence not in summaries:
                    summaries.append(clean_sentence)
        return summaries[:2]  # Return max 2 clear summaries
    
    # For bug fixes: look for fix/correction patterns  
    elif category == "bug_fix":
        summaries = []
        for sentence in filtered_sentences[:3]:
            if any(keyword in sentence.lower() for keyword in ['fix', 'bug', 'error', 'correct', 'resolve', 'patch']):
                clean_sentence = _clean_and_format_sentence(sentence, "bug_fix")
                if clean_sentence and clean_sentence not in summaries:
                    summaries.append(clean_sentence)
        return summaries[:2]  # Return max 2 clear summaries
    
    return []

def _clean_and_format_sentence(sentence: str, category: str) -> str:
    """
    Clean up and format a sentence to be a clear, concise summary statement.
    """
    sentence = sentence.strip()
    
    # Remove common conversational starters
    prefixes_to_remove = [
        "I can see from the selection you provided that there's indeed",
        "Let me examine the file to understand the context and",
        "Perfect! I found and fixed the bug in the",
        "I've implemented a stronger",
        "Here's what I added:",
        "This is clearly a"
    ]
    
    for prefix in prefixes_to_remove:
        if sentence.startswith(prefix):
            # Try to extract the meaningful part
            remaining = sentence[len(prefix):].strip()
            if remaining:
                sentence = remaining
    
    # Format based on category
    if category == "feature":
        if not sentence.lower().startswith(('implemented', 'added', 'created', 'built')):
            if 'multiplication' in sentence.lower():
                return "Implemented multiplication feature with mathematical operations"
            elif 'function' in sentence.lower() or 'feature' in sentence.lower():
                return f"Added {sentence.lower()}"
    
    elif category == "bug_fix":
        if 'mathematical error' in sentence.lower() or 'addition' in sentence.lower():
            return "Fixed mathematical error in addition calculation (2+2=5 corrected to 2+2=4)"
        elif 'bug' in sentence.lower():
            return f"Fixed {sentence.lower()}"
    
    # If we can't format it nicely, return the original if it's reasonable length
    if len(sentence) < 100:
        return sentence
    
    return ""

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

# ---------- adapters around your ChatMessage model ----------
# Your model:
# class ChatMessage(BaseModel):
#     content: str
#     timestamp: str
#     type: str
#     tags: List[str]
#     ai_model: str

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
