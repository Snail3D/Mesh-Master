"""
Token Budget Manager

Provides token estimation and response trimming for bandwidth-constrained
mesh networks. Ensures AI responses fit within chunk size limits (typically 160 chars).

Usage:
    manager = TokenBudgetManager(chunk_size=160, max_chunks=2)
    trimmed = manager.trim_response(ai_response)
"""

import re
import math
from typing import Optional, Tuple


# Simplified token estimation (approximation)
# For production, consider using tiktoken for exact counts
CHARS_PER_TOKEN_AVG = 4  # Conservative estimate for English text


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for given text.

    Uses character-based approximation. For exact counts with specific models,
    integrate tiktoken library.

    Args:
        text: Input text string

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())

    # Approximate tokens (4 chars per token is conservative)
    char_count = len(cleaned)
    return math.ceil(char_count / CHARS_PER_TOKEN_AVG)


def trim_to_budget(text: str, char_budget: int, preserve_sentences: bool = True) -> str:
    """
    Trim text to fit within character budget.

    Args:
        text: Input text to trim
        char_budget: Maximum character count
        preserve_sentences: If True, try to end at sentence boundary

    Returns:
        Trimmed text that fits within budget
    """
    if not text or char_budget <= 0:
        return ""

    if len(text) <= char_budget:
        return text

    # Trim to budget with ellipsis marker
    ellipsis = "..."
    available = char_budget - len(ellipsis)

    if available <= 0:
        return ellipsis

    trimmed = text[:available]

    if preserve_sentences:
        # Try to end at sentence boundary
        sentence_ends = ['.', '!', '?', '\n']
        last_sentence_end = -1

        for end_char in sentence_ends:
            pos = trimmed.rfind(end_char)
            if pos > last_sentence_end:
                last_sentence_end = pos

        # If we found a sentence boundary in the last 20% of text, use it
        if last_sentence_end > available * 0.8:
            trimmed = trimmed[:last_sentence_end + 1]
            return trimmed.strip()

    return trimmed.strip() + ellipsis


class TokenBudgetManager:
    """
    Manages token budgets for AI responses in mesh networks.

    Ensures responses fit within mesh network constraints:
    - Maximum chunk size (typically 160 chars for Meshtastic)
    - Maximum number of chunks to avoid flooding the network

    Attributes:
        chunk_size: Maximum characters per mesh message chunk
        max_chunks: Maximum number of chunks allowed per response
        total_budget: Total character budget (chunk_size * max_chunks)
    """

    def __init__(self, chunk_size: int = 160, max_chunks: int = 2):
        """
        Initialize token budget manager.

        Args:
            chunk_size: Maximum characters per chunk (default 160 for Meshtastic)
            max_chunks: Maximum chunks per response (default 2 to limit bandwidth)
        """
        self.chunk_size = max(1, chunk_size)
        self.max_chunks = max(1, max_chunks)
        self.total_budget = self.chunk_size * self.max_chunks

    def estimate_chunk_count(self, text: str) -> int:
        """
        Estimate how many chunks will be needed for text.

        Args:
            text: Text to estimate

        Returns:
            Number of chunks required
        """
        if not text:
            return 0

        return math.ceil(len(text) / self.chunk_size)

    def fits_budget(self, text: str) -> bool:
        """
        Check if text fits within budget.

        Args:
            text: Text to check

        Returns:
            True if text fits within chunk * max_chunks limit
        """
        return len(text) <= self.total_budget

    def trim_response(self, text: str, preserve_sentences: bool = True) -> str:
        """
        Trim AI response to fit within token budget.

        Args:
            text: AI response to trim
            preserve_sentences: Try to preserve sentence boundaries

        Returns:
            Trimmed response that fits within budget
        """
        return trim_to_budget(text, self.total_budget, preserve_sentences)

    def analyze_response(self, text: str) -> dict:
        """
        Analyze response and provide detailed budget information.

        Args:
            text: Response text to analyze

        Returns:
            Dictionary with analysis:
                - char_count: Total characters
                - chunk_count: Chunks needed
                - fits_budget: Whether it fits
                - trim_needed: Characters to trim
                - token_estimate: Estimated tokens
        """
        char_count = len(text)
        chunk_count = self.estimate_chunk_count(text)
        fits = self.fits_budget(text)
        trim_needed = max(0, char_count - self.total_budget)
        tokens = estimate_tokens(text)

        return {
            'char_count': char_count,
            'chunk_count': chunk_count,
            'fits_budget': fits,
            'trim_needed': trim_needed,
            'token_estimate': tokens,
            'budget_utilization': (char_count / self.total_budget) * 100 if self.total_budget > 0 else 0
        }

    def split_into_chunks(self, text: str) -> list[str]:
        """
        Split text into chunks that fit chunk_size.

        Args:
            text: Text to split

        Returns:
            List of chunk strings
        """
        if not text:
            return []

        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= self.chunk_size:
                chunks.append(remaining)
                break

            # Try to break at word boundary
            chunk = remaining[:self.chunk_size]
            last_space = chunk.rfind(' ')

            if last_space > self.chunk_size * 0.7:  # Found a good break point
                chunks.append(chunk[:last_space])
                remaining = remaining[last_space:].strip()
            else:
                # No good break point, hard break
                chunks.append(chunk)
                remaining = remaining[self.chunk_size:].strip()

        # Limit to max_chunks
        if len(chunks) > self.max_chunks:
            chunks = chunks[:self.max_chunks]
            # Add continuation marker to last chunk
            if chunks:
                chunks[-1] = trim_to_budget(chunks[-1], self.chunk_size, preserve_sentences=True)

        return chunks


# Convenience function for quick integration
def validate_response_for_mesh(response: str, chunk_size: int = 160, max_chunks: int = 2) -> Tuple[bool, Optional[str]]:
    """
    Validate and optionally trim response for mesh network.

    Args:
        response: AI response to validate
        chunk_size: Maximum characters per chunk
        max_chunks: Maximum number of chunks

    Returns:
        Tuple of (fits_without_trimming, trimmed_response_if_needed)
    """
    manager = TokenBudgetManager(chunk_size, max_chunks)

    if manager.fits_budget(response):
        return (True, None)

    trimmed = manager.trim_response(response)
    return (False, trimmed)
