import os
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import models
from services.rag.docs_loader import DocumentLoader
from services.rag.chunks_embed import ChunkEmbedder
from services.rag.rag_models import get_embeddings_model
from utils.logger import logging
from utils.exception import MyException

from config.settings import settings

# ----------------------------------------
# File validation
# ----------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls",
    ".pptx", ".ppt", ".md", ".html", ".htm",
}

# Falls back to 25MB if not configured in settings.rag.max_file_size_mb
MAX_FILE_SIZE_BYTES = getattr(settings.rag, "max_file_size_mb", 25) * 1024 * 1024


def _validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}",
        )

    # UploadFile.file is a SpooledTemporaryFile - safe to seek/tell
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )


# ----------------------------------------
# Embedding model - loaded once at startup, reused across requests
# (singleton lives in rag_models.get_embeddings_model)
# ----------------------------------------


# ----------------------------------------
# Token counting
# ----------------------------------------

def _count_tokens(text: str) -> int:
    """
    Best-effort token count. Uses tiktoken when available (matches how
    most LLM/embedding providers actually tokenize); falls back to a
    whitespace word count, which is only an approximation.
    """
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())


# ----------------------------------------
# Core pipeline
# ----------------------------------------

async def process_and_store_document(
    file: UploadFile,
    company_id: int,
    team_id: Optional[int],
    visibility: str,
    db: AsyncSession,
) -> models.Document:
    """
    Loads, chunks, embeds and persists a document. Used by both the
    company-scoped and team-scoped upload endpoints (and reusable from
    background jobs, CLI tools, or tests since it has no FastAPI
    routing dependency).
    """

    _validate_file(file)

    # 1. Load the document
    logging.info(f"Loading document '{file.filename}' ({visibility} scope)")

    try:
        loader = DocumentLoader()
        docs = await loader.load_document(file)
    except Exception as e:
        logging.exception("Error while loading document.")
        raise MyException(e)

    logging.info("Document loaded successfully")

    # 2. Commit the Document row immediately with status="processing".
    #    This is its own transaction, so a later failure in the
    #    chunking/embedding step can be rolled back WITHOUT wiping out
    #    this record - we still keep a trace of the failed upload.
    document = models.Document(
        company_id=company_id,
        team_id=team_id,
        doc_length=len(docs),
        source=file.filename,
        visibility=visibility,
        status="processing",
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 3. Chunk + embed, in a separate transaction
    try:
        logging.info("Start document chunking and embeddings")

        chunk_embedder = ChunkEmbedder(
            embeddings=get_embeddings_model(),
            config=settings.rag,
        )

        chunks = chunk_embedder.process_documents(docs)

        chunk_rows = [
            models.DocumentChunk(
                company_id=company_id,
                team_id=team_id,
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                page_number=(chunk.get("metadata") or {}).get("page"),
                chunk_text=chunk["text"],
                token_count=_count_tokens(chunk["text"]),
                metadata_json=chunk.get("metadata"),
                embedding=chunk["embedding"],
            )
            for chunk in chunks
        ]

        db.add_all(chunk_rows)

        document.status = "ready"
        await db.commit()
        await db.refresh(document)

        logging.info(
            f"Document '{file.filename}' processed successfully "
            f"with {len(chunk_rows)} chunks."
        )

        return document

    except Exception as e:
        # Rollback only undoes the chunk inserts + status update above,
        # NOT the Document row, since that was already committed in
        # its own transaction in step 2.
        await db.rollback()
        logging.exception("Error while chunking/embedding document.")

        try:
            result = await db.execute(
                select(models.Document).where(models.Document.id == document.id)
            )
            failed_doc = result.scalar_one_or_none()

            if failed_doc is not None:
                failed_doc.status = "failed"
                await db.commit()
        except Exception:
            await db.rollback()
            logging.exception("Failed to mark document as failed.")

        raise MyException(e)


# ----------------------------------------
# Ownership / retrieval helpers
# ----------------------------------------

async def get_owned_document(
    document_id: int,
    db: AsyncSession,
    *,
    visibility: str,
    company_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> models.Document:
    filters = [
        models.Document.id == document_id,
        models.Document.visibility == visibility,
    ]

    if company_id is not None:
        filters.append(models.Document.company_id == company_id)

    if team_id is not None:
        filters.append(models.Document.team_id == team_id)

    result = await db.execute(select(models.Document).where(*filters))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


async def get_owned_document_by_source(
    source: str,
    db: AsyncSession,
    *,
    visibility: str,
    company_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> models.Document:
    """
    Looks a document up by its original filename (the `source` column)
    instead of its numeric id - e.g. for a user typing the file name
    they remember rather than an id they'd have to look up first.

    Case-insensitive exact match. If you later allow duplicate
    filenames per company/team, switch this to return the most
    recent match (order_by(uploaded_at.desc()).limit(1)) instead of
    relying on scalar_one_or_none().
    """
    filters = [
        func.lower(models.Document.source) == source.strip().lower(),
        models.Document.visibility == visibility,
    ]

    if company_id is not None:
        filters.append(models.Document.company_id == company_id)

    if team_id is not None:
        filters.append(models.Document.team_id == team_id)

    result = await db.execute(select(models.Document).where(*filters))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with name '{source}'",
        )

    return document


async def list_documents(
    db: AsyncSession,
    *,
    visibility: str,
    company_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> List[models.Document]:
    filters = [models.Document.visibility == visibility]

    if company_id is not None:
        filters.append(models.Document.company_id == company_id)

    if team_id is not None:
        filters.append(models.Document.team_id == team_id)

    result = await db.execute(
        select(models.Document)
        .where(*filters)
        .order_by(models.Document.uploaded_at.desc())
    )

    return list(result.scalars().all())


async def delete_document(document: models.Document, db: AsyncSession) -> None:
    await db.delete(document)  # cascades to DocumentChunk rows
    await db.commit()


async def replace_document(
    existing_document: models.Document,
    new_file: UploadFile,
    db: AsyncSession,
) -> models.Document:
    """
    "Update" a document matched by name: deletes the existing Document
    row (cascades to its old chunks) and re-runs the full ingestion
    pipeline on the new file, in the same company/team/visibility
    scope as the document it's replacing.
    """
    company_id = existing_document.company_id
    team_id = existing_document.team_id
    visibility = existing_document.visibility

    await db.delete(existing_document)
    await db.commit()

    return await process_and_store_document(
        file=new_file,
        company_id=company_id,
        team_id=team_id,
        visibility=visibility,
        db=db,
    )