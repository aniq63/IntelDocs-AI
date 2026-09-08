import sys
import pytest

from utils.exception import error_message_detail, MyException


class TestErrorMessageDetail:

    def test_returns_formatted_string(self):
        try:
            raise ValueError("test error")
        except ValueError as e:
            msg = error_message_detail(e, sys)
            assert isinstance(msg, str)

    def test_contains_error_message(self):
        try:
            raise ValueError("something broke")
        except ValueError as e:
            msg = error_message_detail(e, sys)
            assert "something broke" in msg

    def test_contains_file_info(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError as e:
            msg = error_message_detail(e, sys)
            assert "Error occurred in python script" in msg

    def test_contains_line_number(self):
        try:
            raise TypeError("bad type")  # this line
        except TypeError as e:
            msg = error_message_detail(e, sys)
            assert "line number" in msg


class TestMyException:

    def test_stores_message(self):
        try:
            raise ValueError("inner error")
        except ValueError as inner:
            exc = MyException(inner, sys)
            assert "inner error" in str(exc)

    def test_is_exception_subclass(self):
        try:
            raise TypeError("test")
        except TypeError as inner:
            exc = MyException(inner, sys)
            assert isinstance(exc, Exception)

    def test_error_message_attribute(self):
        try:
            raise KeyError("missing_key")
        except KeyError as inner:
            exc = MyException(inner, sys)
            assert "missing_key" in exc.error_message

    def test_format_details(self):
        try:
            raise ValueError("details test")
        except ValueError as inner:
            exc = MyException(inner, sys)
            assert "python script" in exc.error_message
            assert "line number" in exc.error_message
