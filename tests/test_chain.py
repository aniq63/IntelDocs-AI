import pytest
from unittest.mock import MagicMock, AsyncMock
from services.rag.chain import RagChain
from services.rag.retrival import RetrievedChunk


def _make_retrieved_chunk(chunk_text="test content", source="test.pdf", **overrides):
    defaults = dict(
        chunk_id=1, document_id=1, chunk_index=0,
        page_number=1, metadata={},
        visibility="company", similarity=0.9,
    )
    defaults.update(overrides)
    return RetrievedChunk(chunk_text=chunk_text, source=source, **defaults)


class TestFormatChunks:

    def _make_chain(self):
        chain = MagicMock(spec=RagChain)
        chain.format_chunks = RagChain.format_chunks.__get__(chain)
        return chain

    def test_empty_chunks(self):
        chain = self._make_chain()
        result = chain.format_chunks([])
        assert result == "No relevant documents were found."

    def test_single_chunk(self):
        chain = self._make_chain()
        chunk = _make_retrieved_chunk(chunk_text="Hello", source="doc.pdf")
        result = chain.format_chunks([chunk])
        assert "Source: doc.pdf" in result
        assert "Hello" in result

    def test_multiple_chunks(self):
        chain = self._make_chain()
        chunks = [
            _make_retrieved_chunk(chunk_text="First", source="a.pdf"),
            _make_retrieved_chunk(chunk_text="Second", source="b.pdf"),
        ]
        result = chain.format_chunks(chunks)
        assert "Source: a.pdf" in result
        assert "Source: b.pdf" in result
        assert "First" in result
        assert "Second" in result

    def test_separator_between_chunks(self):
        chain = self._make_chain()
        chunks = [
            _make_retrieved_chunk(chunk_text="A", source="a.pdf"),
            _make_retrieved_chunk(chunk_text="B", source="b.pdf"),
        ]
        result = chain.format_chunks(chunks)
        # Double newline separates chunks
        assert "A\n\nSource:" in result
