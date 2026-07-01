import os
import tempfile
from pathlib import Path
from fastapi import UploadFile

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
)

from utils.logger import logging
from utils.exception import MyException


class DocumentLoader:
    """
    Load uploaded documents using LangChain loaders and
    return a list of LangChain Document objects.
    """

    def __init__(self):
        self.supported_loaders = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".xls": UnstructuredExcelLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".ppt": UnstructuredPowerPointLoader,
            ".md": UnstructuredMarkdownLoader,
            ".html": UnstructuredHTMLLoader,
            ".htm": UnstructuredHTMLLoader,
        }

    async def load_document(self, file: UploadFile):
        """
        Parameters
        ----------
        file : UploadFile
            File received from FastAPI.

        Returns
        -------
        List[Document]
            LangChain Document objects.
        """

        temp_file_path = None

        try:
            extension = Path(file.filename).suffix.lower()

            if extension not in self.supported_loaders:
                raise ValueError(
                    f"Unsupported file type: {extension}"
                )

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension
            ) as temp_file:

                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            logging.info(
                f"Temporary file created at {temp_file_path}"
            )

            loader_class = self.supported_loaders[extension]
            loader = loader_class(temp_file_path)

            docs = loader.load()

            logging.info(
                f"Successfully loaded {len(docs)} document(s)."
            )

            return docs

        except Exception as e:
            logging.exception("Error while loading document.")
            raise MyException(e)

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logging.info(
                    f"Temporary file removed: {temp_file_path}"
                )