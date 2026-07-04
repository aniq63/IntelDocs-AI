import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq


from config.settings import settings
from utils.exception import MyException


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
 
if not api_key:
            raise MyException(ValueError("GROQ_API_KEY is not set in the environment."))



def embeddings_model():
    """Load and return a cached embedding model."""
    logging.info("Loading embedding model...")

    # Underlying Hugging Face embedding model
    underlying_embeddings = HuggingFaceEmbeddings(
        model_name=settings.rag.embedding_model,
        model_kwargs={"device": "cpu"},  # Change to "cuda" if using a GPU
    )

    # Directory to store cached embeddings
    cache_path = Path(settings.rag.embedding_cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_store = LocalFileStore(str(cache_path))

    # Wrap the model with a cache
    embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=underlying_embeddings,
        document_embedding_cache=cache_store,  # Fixed argument name here
        namespace=settings.rag.embedding_model,
    )

    logging.info("Embedding model loaded successfully.")
    return embeddings



def load_llm_models():
    """Load and return different llm models of GROQ using langchain"""

    grading_llm = ChatGroq(model=settings.rag.grading_model, temperature=0, api_key=api_key)

    rewrite_llm = ChatGroq(model=settings.rag.grading_model, temperature=0.3, api_key=api_key)

    generation_llm = ChatGroq(model=settings.rag.generation_model, temperature=0, api_key=api_key)

    return grading_llm, rewrite_llm , generation_llm


