def estimate_tokens(text: str) -> int:
    """Simple dependency-free token estimate. Good enough for routing economics."""
    if not text:
        return 0
    # English/code mixed prompts average roughly 3.7-4.2 chars per token.
    return max(1, round(len(text) / 4))
