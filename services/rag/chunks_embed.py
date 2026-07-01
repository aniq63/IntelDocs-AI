from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils.logger import logging
from utils.exception import MyException


class ChunkEmbedder:
    """
    Handles:
        1. Document Chunking
        2. Embedding Generation
    """

    def __init__(
        self,
        embeddings,
        config
    ):
        """
        Parameters
        ----------
        embeddings
            HuggingFaceEmbeddings instance.

        config
            RAG configuration loaded from settings.yaml.
        """

        self.embeddings = embeddings
        self.config = config

        logging.info("ChunkEmbedder initialized successfully.")

    def _recursive_chunking(
        self,
        documents: list[Document]
    ) -> list[Document]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.fallback_chunk_size,
            chunk_overlap=self.config.fallback_chunk_overlap
        )

        return splitter.split_documents(documents)

    def _semantic_chunking(
        self,
        documents: list[Document]
    ) -> list[Document]:

        splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type=(
                self.config.breakpoint_threshold_type
            ),
            breakpoint_threshold_amount=(
                self.config.breakpoint_threshold_amount
            )
        )

        chunked_documents = []

        for doc in documents:

            chunks = splitter.create_documents(
                [doc.page_content],
                metadatas=[doc.metadata]
            )

            chunked_documents.extend(chunks)

        return chunked_documents

    def chunk_documents(
        self,
        documents: list[Document]
    ) -> list[Document]:

        try:

            if not self.config.semantic_chunking:

                logging.info(
                    "Using Recursive Character Chunking."
                )

                return self._recursive_chunking(documents)

            logging.info(
                "Using Semantic Chunking."
            )

            chunks = self._semantic_chunking(documents)

            oversized = any(
                len(chunk.page_content)
                > self.config.max_chunk_size
                for chunk in chunks
            )

            if oversized:

                logging.warning(
                    "Large chunks detected. Falling back to Recursive Chunking."
                )

                return self._recursive_chunking(documents)

            return chunks

        except Exception as e:

            logging.exception(
                "Chunking failed."
            )

            raise MyException(e)

    def generate_embeddings(
        self,
        chunked_documents: list[Document]
    ) -> list[dict]:

        try:

            logging.info(
                f"Generating embeddings for {len(chunked_documents)} chunks."
            )

            texts = [
                chunk.page_content
                for chunk in chunked_documents
            ]

            vectors = self.embeddings.embed_documents(texts)

            results = []

            for index, (chunk, vector) in enumerate(
                zip(chunked_documents, vectors)
            ):

                results.append(
                    {
                        "chunk_index": index,
                        "text": chunk.page_content,
                        "embedding": vector,
                        "metadata": chunk.metadata
                    }
                )

            logging.info(
                "Embedding generation completed successfully."
            )

            return results

        except Exception as e:

            logging.exception(
                "Embedding generation failed."
            )

            raise MyException(e)

    def process_documents(
        self,
        documents: list[Document]
    ) -> list[dict]:

        try:

            chunked_documents = self.chunk_documents(
                documents
            )

            return self.generate_embeddings(
                chunked_documents
            )

        except Exception as e:

            logging.exception(
                "Document processing failed."
            )

            raise MyException(e)