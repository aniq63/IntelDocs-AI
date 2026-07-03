import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from services.prompts.contextual_chunking_prompts import (
    CONTEXTUAL_CHUNK_SYSTEM_PROMPT,
    CONTEXTUAL_CHUNK_USER_PROMPT,
)

from utils.logger import logging
from utils.exception import MyException

load_dotenv()


class ChunkEmbedder:
    """
    Handles:
        1. Document Chunking (recursive / semantic)
        2. Contextual Chunking (optional - enriches each chunk with a
           short LLM-generated context note before embedding, using
           Groq as the inference provider)
        3. Embedding Generation
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
            RAG configuration loaded from settings.yaml. Relevant
            fields used here:
                - semantic_chunking: bool
                - fallback_chunk_size / fallback_chunk_overlap
                - breakpoint_threshold_type / breakpoint_threshold_amount
                - max_chunk_size
                - contextual_chunking: bool (default False)
                - contextual_model: str (default "llama-3.1-8b-instant")
                - contextual_max_doc_chars: int (default 20000)
                - contextual_max_workers: int (default 5)
        """

        self.embeddings = embeddings
        self.config = config

        self.contextual_chunking_enabled = getattr(
            config, "contextual_chunking", False
        )

        self.llm = (
            self._init_groq_llm() if self.contextual_chunking_enabled else None
        )

        self._contextual_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUAL_CHUNK_SYSTEM_PROMPT),
                ("human", CONTEXTUAL_CHUNK_USER_PROMPT),
            ]
        )

        logging.info("ChunkEmbedder initialized successfully.")

    # ----------------------------------------
    # Groq LLM setup
    # ----------------------------------------

    def _init_groq_llm(self) -> ChatGroq:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise MyException(
                ValueError(
                    "GROQ_API_KEY is not set. It is required when "
                    "contextual_chunking is enabled in the RAG config."
                )
            )

        return ChatGroq(
            model=getattr(self.config, "contextual_model", "llama-3.1-8b-instant"),
            temperature=0,
            api_key=api_key,
        )

    # ----------------------------------------
    # Chunking strategies
    # ----------------------------------------

    def _recursive_chunking(
        self,
        documents: list[Document]
    ) -> list[Document]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.fallback_chunk_size,
            chunk_overlap=self.config.fallback_chunk_overlap
        )

        return splitter.split_documents(documents)

    def _build_full_text_with_page_map(
        self,
        documents: list[Document]
    ):
        """
        Concatenates all page-level Documents for one uploaded file
        into a single continuous text, and records which character
        offset range came from which page. This lets the semantic
        chunker consider the whole document at once - so a section
        that continues across a page break isn't artificially cut -
        while still letting us recover an approximate page_number per
        resulting chunk afterwards.
        """

        parts = []
        page_map = []  # (start_offset, end_offset, page_number)
        cursor = 0

        source = documents[0].metadata.get("source") if documents else None

        for doc in documents:
            text = doc.page_content
            start = cursor

            parts.append(text)
            cursor += len(text)

            page_map.append((start, cursor, doc.metadata.get("page")))

            parts.append("\n\n")
            cursor += 2

        return "".join(parts), page_map, source

    @staticmethod
    def _page_number_for_offset(page_map, offset):
        if offset is None:
            return None

        for start, end, page_number in page_map:
            if start <= offset < end:
                return page_number

        return page_map[-1][2] if page_map else None

    def _semantic_chunking(
        self,
        documents: list[Document]
    ) -> list[Document]:

        full_text, page_map, source = self._build_full_text_with_page_map(
            documents
        )

        splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type=(
                self.config.breakpoint_threshold_type
            ),
            breakpoint_threshold_amount=(
                self.config.breakpoint_threshold_amount
            )
        )

        raw_chunks = splitter.create_documents([full_text])

        chunked_documents = []
        search_cursor = 0

        for raw_chunk in raw_chunks:
            chunk_text = raw_chunk.page_content

            # SemanticChunker can normalize whitespace slightly, so an
            # exact substring match isn't guaranteed. Try from the
            # last known position first (cheap, usually works since
            # chunks are sequential), then fall back to a global
            # search before giving up on page attribution.
            offset = full_text.find(chunk_text, search_cursor)

            if offset == -1:
                offset = full_text.find(chunk_text)

            page_number = self._page_number_for_offset(page_map, offset)

            if offset != -1:
                search_cursor = offset + len(chunk_text)

            chunked_documents.append(
                Document(
                    page_content=chunk_text,
                    metadata={"source": source, "page": page_number},
                )
            )

        return chunked_documents

    def _split_oversized_chunks(
        self,
        chunks: list[Document]
    ) -> list[Document]:
        """
        Instead of discarding an entire document's semantic chunking
        because ONE chunk came out oversized, only that offending
        chunk gets recursively split further. Every well-sized
        semantic chunk is left untouched.
        """

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.fallback_chunk_size,
            chunk_overlap=self.config.fallback_chunk_overlap,
        )

        final_chunks = []

        for chunk in chunks:
            if len(chunk.page_content) <= self.config.max_chunk_size:
                final_chunks.append(chunk)
                continue

            logging.warning(
                f"Semantic chunk of {len(chunk.page_content)} chars "
                f"exceeded max_chunk_size ({self.config.max_chunk_size}); "
                "splitting it further with recursive chunking."
            )

            final_chunks.extend(splitter.split_documents([chunk]))

        return final_chunks

    def _split_oversized_chunks(
        self,
        chunks: list[Document]
    ) -> list[Document]:
        """
        Semantic chunking can occasionally produce one oversized chunk
        (e.g. a long, semantically uniform section with no strong
        breakpoint). Previously, a single oversized chunk anywhere in
        the document caused ALL chunks to be discarded and replaced
        with blunt fixed-size recursive chunking - destroying good
        semantic boundaries everywhere else in the document to fix a
        problem in one spot.

        Instead: only the oversized chunk(s) get recursively
        re-split. Every chunk that's already within max_chunk_size
        keeps its semantic boundary untouched.
        """

        fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.fallback_chunk_size,
            chunk_overlap=self.config.fallback_chunk_overlap,
        )

        final_chunks: list[Document] = []
        oversized_count = 0

        for chunk in chunks:

            if len(chunk.page_content) > self.config.max_chunk_size:
                oversized_count += 1
                final_chunks.extend(
                    fallback_splitter.split_documents([chunk])
                )
            else:
                final_chunks.append(chunk)

        if oversized_count:
            logging.warning(
                f"{oversized_count} semantic chunk(s) exceeded "
                f"max_chunk_size ({self.config.max_chunk_size} chars) "
                "and were recursively split further; all other "
                "chunks kept their semantic boundaries intact."
            )

        return final_chunks

    # ----------------------------------------
    # Contextual chunking (enrichment step)
    # ----------------------------------------

    def _generate_chunk_context(
        self,
        document_text: str,
        chunk_text: str
    ) -> str:

        messages = self._contextual_prompt.format_messages(
            document=document_text,
            chunk=chunk_text,
        )

        response = self.llm.invoke(messages)

        return response.content.strip()

    def _contextualize_chunk(
        self,
        chunk: Document,
        full_document_text: str
    ) -> Document:

        try:
            context = self._generate_chunk_context(
                full_document_text,
                chunk.page_content,
            )

            enriched_content = f"{context}\n\n{chunk.page_content}"

        except Exception:
            logging.exception(
                "Contextual chunking failed for a chunk; "
                "falling back to the original chunk text."
            )

            context = None
            enriched_content = chunk.page_content

        metadata = dict(chunk.metadata)
        metadata["original_text"] = chunk.page_content

        if context:
            metadata["context"] = context

        return Document(page_content=enriched_content, metadata=metadata)

    def _apply_contextual_chunking(
        self,
        documents: list[Document],
        chunks: list[Document]
    ) -> list[Document]:

        max_doc_chars = getattr(self.config, "contextual_max_doc_chars", 20000)
        max_workers = getattr(self.config, "contextual_max_workers", 5)

        full_document_text = "\n\n".join(
            doc.page_content for doc in documents
        )[:max_doc_chars]

        logging.info(
            f"Applying contextual chunking to {len(chunks)} chunk(s) "
            f"using Groq model "
            f"'{getattr(self.config, 'contextual_model', 'llama-3.1-8b-instant')}'."
        )

        contextualized_chunks: list[Document] = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            future_to_index = {
                executor.submit(
                    self._contextualize_chunk, chunk, full_document_text
                ): index
                for index, chunk in enumerate(chunks)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                contextualized_chunks[index] = future.result()

        logging.info("Contextual chunking completed.")

        return contextualized_chunks

    # ----------------------------------------
    # Public chunking entry point
    # ----------------------------------------

    def chunk_documents(
        self,
        documents: list[Document]
    ) -> list[Document]:

        try:

            if not self.config.semantic_chunking:

                logging.info(
                    "Using Recursive Character Chunking."
                )

                chunks = self._recursive_chunking(documents)

            else:

                logging.info(
                    "Using Semantic Chunking."
                )

                chunks = self._semantic_chunking(documents)

                chunks = self._split_oversized_chunks(chunks)

            if self.contextual_chunking_enabled:
                chunks = self._apply_contextual_chunking(documents, chunks)

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