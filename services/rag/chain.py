from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from utils.logger import logging
from utils.exception import MyException

from services.rag.rag_models import load_llm_models
from services.rag.retrival import RetrievalService, RetrievedChunk
from services.prompts.rag_chain_prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_HUMAN_PROMPT,
    build_scope_description,
)


class RagChain:

    def __init__(
        self,
        db: AsyncSession,
        company_id: int,
        company_name: str,
        team_id: Optional[int] = None,
        team_name: Optional[str] = None,
        top_k: int = 6,
        min_similarity: float = 0.15,
    ):
        self.db = db
        self.company_id = company_id
        self.team_id = team_id
        self.top_k = top_k
        self.min_similarity = min_similarity

        self.scope = build_scope_description(company_name, team_name)

        self.retrieval_service = RetrievalService(db)

        # Only the generation model is needed here (no grading/rewrite
        # step in the simple chain).
        self.llm = load_llm_models()

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", RAG_SYSTEM_PROMPT), ("human", RAG_HUMAN_PROMPT)]
        )

    # -------------------------------------------------
    # Retrieve chunks
    # -------------------------------------------------
    async def retriever(self, question: str) -> list[RetrievedChunk]:
        logging.info(f"[rag_chain] retrieving for: {question!r}")

        chunks = await self.retrieval_service.retrieve(
            question=question,
            company_id=self.company_id,
            team_id=self.team_id,
            top_k=self.top_k,
            min_similarity=self.min_similarity,
        )

        logging.info(f"[rag_chain] retrieved {len(chunks)} chunk(s)")

        return chunks

    # -------------------------------------------------
    # Format chunks into context text
    # -------------------------------------------------
    def format_chunks(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No relevant documents were found."

        return "\n\n".join(
            f"Source: {chunk.source}\n{chunk.chunk_text}"
            for chunk in chunks
        )

    async def get_context(self, question: str) -> str:
        chunks = await self.retriever(question)
        return self.format_chunks(chunks)

    # -------------------------------------------------
    # Run the chain
    # -------------------------------------------------
    async def ask(self, question: str) -> str:
        if not question or not question.strip():
            raise MyException(ValueError("Question must not be empty."))

        try:
            logging.info("[rag_chain] starting")

            rag_chain = (
                {
                    "context": RunnableLambda(self.get_context),
                    "question": RunnablePassthrough(),
                    "scope": lambda _: self.scope,
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )

            answer = await rag_chain.ainvoke(question)

            logging.info("[rag_chain] completed")

            return answer

        except Exception as e:
            logging.exception("RagChain failed.")
            raise MyException(e)