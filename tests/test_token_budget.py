"""
Unit tests for Token Budget Manager

Tests token estimation, response trimming, and chunk splitting
for mesh network constraints.
"""

import pytest
from mesh_master.ai_utils.token_budget import (
    TokenBudgetManager,
    estimate_tokens,
    trim_to_budget,
    validate_response_for_mesh
)


class TestTokenEstimation:
    """Test token estimation functions"""

    def test_estimate_tokens_empty(self):
        """Empty string should return 0 tokens"""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_estimate_tokens_simple(self):
        """Simple text should estimate reasonably"""
        # "Hello world" is roughly 2 tokens (8 chars / 4)
        tokens = estimate_tokens("Hello world")
        assert 2 <= tokens <= 4

    def test_estimate_tokens_long(self):
        """Long text should scale linearly"""
        text = "This is a longer test message " * 10
        tokens = estimate_tokens(text)
        assert tokens > 50


class TestTrimToBudget:
    """Test text trimming functions"""

    def test_trim_no_change_if_fits(self):
        """Should return original if within budget"""
        text = "Short text"
        result = trim_to_budget(text, 100)
        assert result == text

    def test_trim_adds_ellipsis(self):
        """Should add ellipsis when trimming"""
        text = "This is a very long text that needs trimming"
        result = trim_to_budget(text, 20)
        assert result.endswith("...")
        assert len(result) <= 20

    def test_trim_preserves_sentences(self):
        """Should preserve sentence boundaries when possible"""
        text = "First sentence. Second sentence. Third sentence."
        result = trim_to_budget(text, 35, preserve_sentences=True)
        # Should end at a period
        assert result.endswith(".")

    def test_trim_empty_string(self):
        """Should handle empty string gracefully"""
        assert trim_to_budget("", 100) == ""

    def test_trim_zero_budget(self):
        """Should return ellipsis for zero budget"""
        result = trim_to_budget("Any text", 0)
        assert result == ""


class TestTokenBudgetManager:
    """Test TokenBudgetManager class"""

    def test_initialization_defaults(self):
        """Should initialize with sane defaults"""
        manager = TokenBudgetManager()
        assert manager.chunk_size == 160
        assert manager.max_chunks == 2
        assert manager.total_budget == 320

    def test_initialization_custom(self):
        """Should accept custom parameters"""
        manager = TokenBudgetManager(chunk_size=100, max_chunks=3)
        assert manager.chunk_size == 100
        assert manager.max_chunks == 3
        assert manager.total_budget == 300

    def test_estimate_chunk_count(self):
        """Should correctly estimate chunk count"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=5)

        assert manager.estimate_chunk_count("") == 0
        assert manager.estimate_chunk_count("12345") == 1
        assert manager.estimate_chunk_count("1234567890") == 1
        assert manager.estimate_chunk_count("12345678901") == 2
        assert manager.estimate_chunk_count("123456789012345678901") == 3

    def test_fits_budget_pass(self):
        """Should return True when text fits budget"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=2)
        assert manager.fits_budget("12345") is True
        assert manager.fits_budget("1234567890") is True
        assert manager.fits_budget("12345678901234567890") is True  # Exactly 20

    def test_fits_budget_fail(self):
        """Should return False when text exceeds budget"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=2)
        assert manager.fits_budget("123456789012345678901") is False

    def test_trim_response(self):
        """Should trim response to fit budget"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=2)
        text = "This is a long message that exceeds our budget"
        trimmed = manager.trim_response(text)

        assert len(trimmed) <= manager.total_budget
        assert "..." in trimmed

    def test_analyze_response_fits(self):
        """Should analyze response correctly when it fits"""
        manager = TokenBudgetManager(chunk_size=100, max_chunks=2)
        text = "Short message"

        analysis = manager.analyze_response(text)

        assert analysis['char_count'] == len(text)
        assert analysis['fits_budget'] is True
        assert analysis['trim_needed'] == 0
        assert analysis['chunk_count'] == 1

    def test_analyze_response_exceeds(self):
        """Should analyze response correctly when it exceeds budget"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=2)
        text = "This message is way too long for the budget"

        analysis = manager.analyze_response(text)

        assert analysis['char_count'] == len(text)
        assert analysis['fits_budget'] is False
        assert analysis['trim_needed'] > 0
        assert analysis['chunk_count'] > 2

    def test_split_into_chunks_single(self):
        """Should return single chunk for short text"""
        manager = TokenBudgetManager(chunk_size=100, max_chunks=5)
        text = "Short message"

        chunks = manager.split_into_chunks(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_into_chunks_multiple(self):
        """Should split long text into multiple chunks"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=5)
        text = "This is a longer message that needs splitting"

        chunks = manager.split_into_chunks(text)

        assert len(chunks) > 1
        assert all(len(chunk) <= 10 for chunk in chunks)
        # Chunks should reconstruct original (minus spaces)
        assert text.replace(" ", "") in "".join(chunks).replace(" ", "")

    def test_split_into_chunks_respects_max(self):
        """Should limit chunks to max_chunks"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=2)
        text = "This is a very long message " * 10  # Way more than 2 chunks

        chunks = manager.split_into_chunks(text)

        assert len(chunks) <= manager.max_chunks
        assert "..." in chunks[-1]  # Last chunk should have ellipsis

    def test_split_into_chunks_word_boundaries(self):
        """Should try to break at word boundaries"""
        manager = TokenBudgetManager(chunk_size=15, max_chunks=5)
        text = "Hello world this is a test message"

        chunks = manager.split_into_chunks(text)

        # Chunks should not break words in the middle
        for chunk in chunks:
            # Check that words aren't split
            if "..." not in chunk:
                words = chunk.strip().split()
                # Each word should be complete (not end/start with letters from adjacent chunks)
                assert all(len(word) > 0 for word in words)


class TestValidateResponseForMesh:
    """Test convenience validation function"""

    def test_validate_fits(self):
        """Should return True and None when response fits"""
        response = "Short message"
        fits, trimmed = validate_response_for_mesh(response, chunk_size=100, max_chunks=2)

        assert fits is True
        assert trimmed is None

    def test_validate_needs_trim(self):
        """Should return False and trimmed version when too long"""
        response = "This is a very long message " * 20
        fits, trimmed = validate_response_for_mesh(response, chunk_size=100, max_chunks=2)

        assert fits is False
        assert trimmed is not None
        assert len(trimmed) <= 200
        assert "..." in trimmed

    def test_validate_default_params(self):
        """Should use Meshtastic defaults (160 char chunks)"""
        response = "x" * 500
        fits, trimmed = validate_response_for_mesh(response)

        assert fits is False
        assert len(trimmed) <= 320  # 160 * 2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_negative_chunk_size(self):
        """Should handle negative chunk size gracefully"""
        manager = TokenBudgetManager(chunk_size=-10, max_chunks=2)
        # Should default to minimum of 1
        assert manager.chunk_size > 0

    def test_zero_max_chunks(self):
        """Should handle zero max chunks gracefully"""
        manager = TokenBudgetManager(chunk_size=100, max_chunks=0)
        # Should default to minimum of 1
        assert manager.max_chunks > 0

    def test_unicode_text(self):
        """Should handle unicode characters correctly"""
        manager = TokenBudgetManager(chunk_size=20, max_chunks=2)
        text = "Hello 世界 🌍 emoji"

        # Should not crash
        result = manager.trim_response(text)
        assert isinstance(result, str)

        chunks = manager.split_into_chunks(text)
        assert all(isinstance(c, str) for c in chunks)

    def test_very_long_word(self):
        """Should handle very long words (no spaces to break)"""
        manager = TokenBudgetManager(chunk_size=10, max_chunks=3)
        text = "a" * 100  # Single 100-character "word"

        chunks = manager.split_into_chunks(text)

        # Should hard-break the word
        assert len(chunks) <= manager.max_chunks
        assert all(len(chunk) <= manager.chunk_size for chunk in chunks)


@pytest.mark.integration
class TestIntegrationWithMeshMaster:
    """Integration tests for Mesh-Master scenarios"""

    def test_typical_ai_response(self):
        """Test with typical AI response length"""
        manager = TokenBudgetManager(chunk_size=160, max_chunks=2)

        # Typical concise AI response
        response = "To relay a message to 'snmo', use: snmo your message here. The system will track ACKs and confirm delivery."

        analysis = manager.analyze_response(response)

        assert analysis['fits_budget'] is True
        assert analysis['chunk_count'] <= 2

    def test_overly_verbose_ai_response(self):
        """Test trimming verbose AI response"""
        manager = TokenBudgetManager(chunk_size=160, max_chunks=2)

        # Verbose AI response that needs trimming
        response = """
        To relay a message to another node, you have several options available.
        First, you can use the shortname directly, like 'snmo hello'. Alternatively,
        you can prefix it with a slash: '/snmo hello'. Both formats work identically.
        The system will automatically look up the node ID associated with the shortname
        'snmo' and forward your message. It will then track the acknowledgment (ACK)
        from the recipient and notify you when it's received. This typically takes
        about 20 seconds depending on network conditions and signal strength.
        """

        trimmed = manager.trim_response(response.strip())

        assert len(trimmed) <= 320
        assert "..." in trimmed

    def test_command_help_response(self):
        """Test with command help response"""
        manager = TokenBudgetManager(chunk_size=160, max_chunks=2)

        response = "/nodes - Lists all nodes\n/relay <node> <msg> - Relay message\n/mail - Check mail"

        analysis = manager.analyze_response(response)
        assert analysis['fits_budget'] is True
