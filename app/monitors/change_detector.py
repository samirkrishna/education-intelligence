
import hashlib
import difflib
import re


def normalize_content(content: str) -> str:
    # Normalize whitespace
    content = re.sub(r"\s+", " ", content)

    return content.strip()


def calculate_hash(content: str) -> str:
    normalized = normalize_content(content)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def compare_content(old_content: str, new_content: str) -> dict:

    old_normalized = normalize_content(old_content)
    new_normalized = normalize_content(new_content)

    old_hash = calculate_hash(old_normalized)
    new_hash = calculate_hash(new_normalized)

    changed = old_hash != new_hash

    differences = list(
        difflib.unified_diff(
            old_normalized.split(),
            new_normalized.split(),
            fromfile="previous",
            tofile="current",
            lineterm="",
            n=3
        )
    )

    return {
        "changed": changed,
        "old_hash": old_hash,
        "new_hash": new_hash,
        "differences": differences[:50]
    }
