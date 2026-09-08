import pytest

from services.rag.retrival import _to_pgvector_literal, RetrievedChunk


class TestToPgvectorLiteral:

    def test_basic_embedding(self):
        result = _to_pgvector_literal([0.1, 0.2, 0.3])
        assert result.startswith("[")
        assert result.endswith("]")

    def test_comma_separated(self):
        result = _to_pgvector_literal([0.1, 0.2])
        parts = result.strip("[]").split(",")
        assert len(parts) == 2

    def test_precision(self):
        result = _to_pgvector_literal([1.0 / 3.0])
        # 8 decimal places
        assert "0.33333333" in result

    def test_negative_values(self):
        result = _to_pgvector_literal([-0.5, 0.5])
        assert "-0.50000000" in result
        assert "0.50000000" in result

    def test_zero_values(self):
        result = _to_pgvector_literal([0.0, 0.0])
        assert "0.00000000" in result

    def test_empty_list(self):
        result = _to_pgvector_literal([])
        assert result == "[]"

    def test_single_value(self):
        result = _to_pgvector_literal([1.0])
        assert result == "[1.00000000]"

    def test_384_dimension(self):
        emb = [0.01] * 384
        result = _to_pgvector_literal(emb)
        assert result.startswith("[")
        assert result.endswith("]")
        parts = result.strip("[]").split(",")
        assert len(parts) == 384


class TestRetrievedChunk:

    def test_dataclass_creation(self):
        chunk = RetrievedChunk(
            chunk_id=1, document_id=2, chunk_index=0,
            page_number=1, chunk_text="hello world",
            metadata={}, source="test.pdf",
            visibility="company", similarity=0.95,
        )
        assert chunk.chunk_text == "hello world"
        assert chunk.similarity == 0.95

    def test_optional_page_number(self):
        chunk = RetrievedChunk(
            chunk_id=1, document_id=2, chunk_index=0,
            page_number=None, chunk_text="text",
            metadata=None, source="f.txt",
            visibility="team", similarity=0.5,
        )
        assert chunk.page_number is None

    def test_metadata_optional(self):
        chunk = RetrievedChunk(
            chunk_id=1, document_id=1, chunk_index=0,
            page_number=None, chunk_text="x",
            metadata=None, source="x",
            visibility="company", similarity=0.0,
        )
        assert chunk.metadata is None
