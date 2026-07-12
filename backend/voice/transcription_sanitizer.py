"""
Speech Transcription Text Sanitizer
Removes filler words, cleans Unicode punctuation, and normalizes Hindi-English transcripts.
"""

import re

FILLER_WORDS = {
    "uh", "um", "ah", "like", "you know", "basically", 
    "actually", "hain na", "toh", "matlab"
}

def sanitize_transcription(raw_text: str) -> str:
    if not raw_text:
        return ""

    # Normalize whitespace
    text = " ".join(raw_text.strip().split())

    # Remove repeated punctuation
    text = re.sub(r'([.!?])+', r'', text)

    # Clean leading filler interjections
    tokens = text.split()
    while tokens and tokens[0].lower() in FILLER_WORDS:
        tokens.pop(0)

    cleaned = " ".join(tokens)
    return cleaned
