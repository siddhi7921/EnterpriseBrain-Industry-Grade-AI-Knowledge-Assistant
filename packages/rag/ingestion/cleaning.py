from __future__ import annotations

import re
import unicodedata


_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)disregard\s+(all\s+)?system\s+prompts?",
    r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
    r"(?i)reveal\s+(your\s+)?system\s+prompt",
]


def clean_text(raw_text: str) -> str:
    """Normalize Unicode characters, collapse redundant whitespace, and strip control artifacts."""
    if not raw_text:
        return ""
    text = unicodedata.normalize("NFKC", raw_text)
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^\s*(?:page\s+\d+(?:\s+of\s+\d+)?|-\s*\d+\s*-)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def neutralize_prompt_injection(text: str) -> str:
    """Neutralize overt prompt injection directives inside untrusted document text."""
    sanitized = text
    for pattern in _INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[UNTRUSTED_DOCUMENT_DIRECTIVE_REDACTED]", sanitized)
    return sanitized
