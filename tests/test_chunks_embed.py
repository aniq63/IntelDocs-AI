import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

from services.rag.chunks_embed import ChunkEmbedder
from config.settings import RAGConfig


def _make_chunk_embedder(**overrides):
    cfg_dict = {
        "semantic_chunking": False,
        "fallback_chunk_size": 400,
        "fallback_chunk_overlap": 80,
        "max_chunk_size": 800,
        "breakpoint_threshold_type": "percentile",
        "breakpoint_threshold_amount": 80,
        "contextual_chunking": False,
        "contextual_model": "test-model",
        "contextual_max_doc_chars": 20000,
        "contextual_max_workers": 5,
    }
    cfg_dict.update(overrides)

    # Build a real RAGConfig-like object
    cfg = MagicMock()
    for k, v in cfg_dict.items():
        setattr(cfg, k, v)

    embeddings = MagicMock()
    return ChunkEmbedder(embeddings=embeddings, config=cfg)


class TestRecursiveChunking:

    def test_basic_splitting(self):
        ce = _make_chunk_embedder(
            semantic_chunking=False,
            fallback_chunk_size=100,
            fallback_chunk_overlap=20,
        )
        docs = [
            Document(page_content="word " * 50, metadata={"source": "test.txt"})
        ]
        chunks = ce._recursive_chunking(docs)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.page_content) <= 120  # some tolerance

    def test_preserves_metadata(self):
        ce = _make_chunk_embedder(
            semantic_chunking=False,
            fallback_chunk_size=50,
            fallback_chunk_overlap=10,
        )
        docs = [
            Document(page_content="Hello world " * 20, metadata={"source": "a.txt", "page": 1})
        ]
        chunks = ce._recursive_chunking(docs)
        for chunk in chunks:
            assert "source" in chunk.metadata


class TestBuildFullTextWithPageMap:

    def test_single_page(self):
        ce = _make_chunk_embedder()
        docs = [
            Document(page_content="Page one content", metadata={"page": 1, "source": "f.pdf"})
        ]
        full_text, page_map, source = ce._build_full_text_with_page_map(docs)
        assert "Page one content" in full_text
        assert len(page_map) == 1
        assert source == "f.pdf"

    def test_multi_page(self):
        ce = _make_chunk_embedder()
        docs = [
            Document(page_content="Page 1", metadata={"page": 1, "source": "f.pdf"}),
            Document(page_content="Page 2", metadata={"page": 2, "source": "f.pdf"}),
        ]
        full_text, page_map, source = ce._build_full_text_with_page_map(docs)
        assert "Page 1" in full_text
        assert "Page 2" in full_text
        assert len(page_map) == 2
        # Second page starts after first
        assert page_map[1][0] > page_map[0][0]

    def test_source_from_first_doc(self):
        ce = _make_chunk_embedder()
        docs = [
            Document(page_content="A", metadata={"source": "x.pdf"}),
            Document(page_content="B", metadata={"source": "y.pdf"}),
        ]
        _, _, source = ce._build_full_text_with_page_map(docs)
        assert source == "x.pdf"


class TestPageNumberForOffset:

    def test_exact_start(self):
        page_map = [(0, 10, 1), (10, 20, 2)]
        assert ChunkEmbedder._page_number_for_offset(page_map, 0) == 1

    def test_in_second_page(self):
        page_map = [(0, 10, 1), (10, 20, 2)]
        assert ChunkEmbedder._page_number_for_offset(page_map, 15) == 2

    def test_none_offset(self):
        page_map = [(0, 10, 1)]
        assert ChunkEmbedder._page_number_for_offset(page_map, None) is None

    def test_empty_page_map(self):
        assert ChunkEmbedder._page_number_for_offset([], 5) is None

    def test_offset_beyond_end(self):
        page_map = [(0, 10, 1)]
        # Falls back to last page
        assert ChunkEmbedder._page_number_for_offset(page_map, 100) == 1


class TestSplitOversizedChunks:

    def test_no_oversized(self):
        ce = _make_chunk_embedder(
            fallback_chunk_size=400,
            fallback_chunk_overlap=80,
            max_chunk_size=800,
        )
        chunks = [
            Document(page_content="short", metadata={}),
            Document(page_content="also short", metadata={}),
        ]
        result = ce._split_oversized_chunks(chunks)
        assert len(result) == 2

    def test_oversized_gets_split(self):
        ce = _make_chunk_embedder(
            fallback_chunk_size=100,
            fallback_chunk_overlap=20,
            max_chunk_size=50,
        )
        big_text = "word " * 50  # ~250 chars
        chunks = [
            Document(page_content=big_text, metadata={}),
        ]
        result = ce._split_oversized_chunks(chunks)
        assert len(result) > 1

    def test_mixed_sizes(self):
        ce = _make_chunk_embedder(
            fallback_chunk_size=50,
            fallback_chunk_overlap=10,
            max_chunk_size=30,
        )
        chunks = [
            Document(page_content="tiny", metadata={}),
            Document(page_content="x " * 50, metadata={}),
            Document(page_content="tiny2", metadata={}),
        ]
        result = ce._split_oversized_chunks(chunks)
        # The tiny ones pass through, the big one splits
        assert len(result) >= 3


class TestChunkDocumentsRecursive:

    def test_recursive_mode(self):
        ce = _make_chunk_embedder(
            semantic_chunking=False,
            fallback_chunk_size=100,
            fallback_chunk_overlap=20,
        )
        docs = [Document(page_content="Hello world " * 30, metadata={"source": "t.txt"})]
        chunks = ce.chunk_documents(docs)
        assert len(chunks) >= 1
