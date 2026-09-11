import pytest
from sqlalchemy.engine.url import make_url

from config.settings import RAGConfig, Settings
from database.connection import normalize_database_url


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


def test_supabase_pooler_url_is_normalized_for_asyncpg():
    original = (
        "postgresql+psycopg://postgres.qgmrtjxffiwuiyoysbbx:"
        "password@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
    )

    normalized = normalize_database_url(original)
    url = make_url(normalized)

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "aws-1-ap-northeast-2.pooler.supabase.com"
    assert url.port == 6543
    assert url.query["sslmode"] == "require"
    assert "pgbouncer" not in url.query
