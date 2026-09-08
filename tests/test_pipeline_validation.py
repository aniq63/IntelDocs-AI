import io
import os
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from services.pipeline.knowledge_service_pipeline import (
    _validate_file,
    _count_tokens,
    ALLOWED_EXTENSIONS,
)


def _make_uploadfile(filename: str, content: bytes = b"hello world"):
    spool = io.BytesIO(content)
    file = MagicMock()
    file.filename = filename
    file.file = spool
    return file


class TestValidateFile:

    def test_valid_pdf(self):
        f = _make_uploadfile("doc.pdf", b"pdf content")
        # Should not raise
        _validate_file(f)

    def test_valid_txt(self):
        f = _make_uploadfile("readme.txt")
        _validate_file(f)

    def test_valid_docx(self):
        f = _make_uploadfile("report.docx")
        _validate_file(f)

    def test_valid_csv(self):
        f = _make_uploadfile("data.csv")
        _validate_file(f)

    def test_valid_md(self):
        f = _make_uploadfile("notes.md")
        _validate_file(f)

    def test_valid_xlsx(self):
        f = _make_uploadfile("sheet.xlsx")
        _validate_file(f)

    def test_valid_pptx(self):
        f = _make_uploadfile("slides.pptx")
        _validate_file(f)

    def test_valid_html(self):
        f = _make_uploadfile("page.html")
        _validate_file(f)

    def test_invalid_extension(self):
        f = _make_uploadfile("image.png")
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(f)
        assert exc_info.value.status_code == 400
        assert "Unsupported" in exc_info.value.detail

    def test_invalid_exe(self):
        f = _make_uploadfile("malware.exe")
        with pytest.raises(HTTPException):
            _validate_file(f)

    def test_empty_file(self):
        f = _make_uploadfile("empty.pdf", b"")
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(f)
        assert "empty" in exc_info.value.detail.lower()

    def test_no_filename(self):
        f = _make_uploadfile("")
        f.filename = None
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(f)
        assert exc_info.value.status_code == 400

    def test_allowed_extensions_set(self):
        expected = {
            ".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls",
            ".pptx", ".ppt", ".md", ".html", ".htm",
        }
        assert ALLOWED_EXTENSIONS == expected

    def test_case_insensitive_extension(self):
        f = _make_uploadfile("DOC.PDF")
        # The extension check uses .lower(), so uppercase should work
        _validate_file(f)

    def test_ppt_extension(self):
        f = _make_uploadfile("old.ppt")
        _validate_file(f)

    def test_htm_extension(self):
        f = _make_uploadfile("old.htm")
        _validate_file(f)


class TestCountTokens:

    def test_simple_text(self):
        count = _count_tokens("Hello world this is a test")
        assert count > 0

    def test_empty_string(self):
        count = _count_tokens("")
        assert count >= 0

    def test_single_word(self):
        count = _count_tokens("hello")
        assert count >= 1

    def test_returns_integer(self):
        assert isinstance(_count_tokens("test"), int)

    def test_longer_text_more_tokens(self):
        short = _count_tokens("hello")
        long = _count_tokens("hello world this is a much longer sentence with many words")
        assert long > short
