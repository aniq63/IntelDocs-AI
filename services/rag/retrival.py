import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import logging
from utils.exception import MyException

from services.rag.rag_models import embeddings_model


@dataclass
class RetrievedChunk:
    """
    Structured result for a single retrieved chunk, instead of a raw
    RowMapping - makes downstream code (an API route, a prompt
    builder, etc.) easier to work with and type-check.
    """

    chunk_id: int
    document_id: int
    chunk_index: int
    page_number: Optional[int]
    chunk_text: str
    metadata: Optional[dict]
    source: str
    visibility: str
    similarity: float


def _to_pgvector_literal(embedding: List[float]) -> str:
    """
    asyncpg has no built-in codec for pgvector, so a Python list bound
    as a parameter won't automatically cast to `vector`. Serializing
    it to pgvector's own text format ("[0.1,0.2,...]") and letting
    Postgres CAST(:embedding AS vector) parse that string works
    reliably regardless of driver.
    """
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


class RetrievalService:
    """
    Handles semantic retrieval over document_chunks using pgvector
    cosine similarity, scoped to a company (and optionally a team).
    """

    # Cached across instances so the embedding model is loaded once
    # per process rather than once per RetrievalService() call.
    _embedding_model = None

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_model = self._get_embedding_model()

    @classmethod
    def _get_embedding_model(cls):
        if cls._embedding_model is None:
            logging.info("Loading embedding model for retrieval (first use).")
            cls._embedding_model = embeddings_model()

        return cls._embedding_model

    async def search_pgvector(
        self,
        query_embedding: List[float],
        company_id: int,
        team_id: Optional[int],
        top_k: int = 5,
        min_similarity: float = 0.30,
    ) -> List[RetrievedChunk]:
        """
        Retrieve the most relevant chunks using cosine similarity.

        Visibility rules:
          - "company" visibility chunks are always eligible.
          - "team" visibility chunks are only eligible when team_id
            is provided and matches dc.team_id.
        """

        top_k = max(1, min(top_k, 50))
        min_similarity = max(0.0, min(min_similarity, 1.0))

        sql = text(
            """
            SELECT

                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_index,
                dc.page_number,
                dc.chunk_text,
                dc.metadata,

                d.source,
                d.visibility,

                1 - (
                    dc.embedding <=> CAST(:embedding AS vector)
                ) AS similarity

            FROM document_chunks dc

            INNER JOIN documents d
                ON d.id = dc.document_id

            WHERE

                d.status = 'ready'

                AND dc.company_id = CAST(:company_id AS bigint)

                AND
                (
                    d.visibility = 'company'

                    OR

                    (
                        d.visibility = 'team'
                        AND CAST(:team_id AS bigint) IS NOT NULL
                        AND dc.team_id = CAST(:team_id AS bigint)
                    )
                )

                AND
                (
                    1 - (
                        dc.embedding <=> CAST(:embedding AS vector)
                    )
                ) >= CAST(:min_similarity AS float8)

            ORDER BY
                dc.embedding <=> CAST(:embedding AS vector)

            LIMIT CAST(:top_k AS int)
            """
        )

        try:
            result = await self.db.execute(
                sql,
                {
                    "embedding": _to_pgvector_literal(query_embedding),
                    "company_id": company_id,
                    "team_id": team_id,
                    "top_k": top_k,
                    "min_similarity": min_similarity,
                },
            )

            rows = result.mappings().all()

        except Exception as e:
            logging.exception("pgvector similarity search failed.")
            raise MyException(e)

        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                chunk_index=row["chunk_index"],
                page_number=row["page_number"],
                chunk_text=row["chunk_text"],
                metadata=row["metadata"],
                source=row["source"],
                visibility=row["visibility"],
                similarity=float(row["similarity"]),
            )
            for row in rows
        ]

    async def retrieve(
        self,
        question: str,
        company_id: int,
        team_id: Optional[int],
        top_k: int = 5,
        min_similarity: float = 0.30,
    ) -> List[RetrievedChunk]:
        """
        Convert the question into an embedding and retrieve the most
        relevant chunks.
        """

        if not question or not question.strip():
            raise MyException(ValueError("Query text must not be empty."))

        try:
            # embed_query is a blocking call (HuggingFace/sentence
            # transformers) - push it off the event loop so it
            # doesn't block other concurrent requests.
            query_embedding = await asyncio.to_thread(
                self.embedding_model.embed_query, question
            )
        except Exception as e:
            logging.exception("Failed to embed the query.")
            raise MyException(e)

        return await self.search_pgvector(
            query_embedding=query_embedding,
            company_id=company_id,
            team_id=team_id,
            top_k=top_k,
            min_similarity=min_similarity,
        )