import pytest

from config.settings import RAGConfig, Settings


class TestRAGConfig:

    def test_defaults(self):
        cfg = RAGConfig()
        assert cfg.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert cfg.semantic_chunking is True
        assert cfg.fallback_chunk_size == 400
        assert cfg.fallback_chunk_overlap == 80
        assert cfg.max_chunk_size == 800
        assert cfg.embedding_dimension == 384
        assert cfg.contextual_chunking is False

    def test_frozen(self):
        cfg = RAGConfig()
        with pytest.raises(AttributeError):
            cfg.embedding_model = "different-model"

    def test_custom_values(self):
        cfg = RAGConfig(
            fallback_chunk_size=200,
            fallback_chunk_overlap=40,
            max_chunk_size=500,
            contextual_chunking=True,
        )
        assert cfg.fallback_chunk_size == 200
        assert cfg.fallback_chunk_overlap == 40
        assert cfg.max_chunk_size == 500
        assert cfg.contextual_chunking is True

    def test_breakpoint_defaults(self):
        cfg = RAGConfig()
        assert cfg.breakpoint_threshold_type == "percentile"
        assert cfg.breakpoint_threshold_amount == 80


class TestSettings:

    def test_has_rag(self):
        s = Settings()
        assert isinstance(s.rag, RAGConfig)

    def test_rag_config_is_same_instance(self):
        s = Settings()
        assert s.rag is s.rag

    def test_llm_model_on_rag_config(self):
        cfg = RAGConfig()
        assert cfg.llm_model == "openai/gpt-oss-20b"
