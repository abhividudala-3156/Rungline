def estimate_tokens(text: str) -> int:
    """Rough planning estimate only; not a provider billing measurement."""
    return max(1, len(text) // 4)
