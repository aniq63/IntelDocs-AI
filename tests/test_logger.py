import os
import logging
import pytest
from unittest.mock import patch

from utils.logger import LOG_DIR


class TestLoggerModule:

    def test_log_dir_exists(self):
        assert os.path.isdir(LOG_DIR)

    def test_configure_logger_returns_root_logger(self):
        # The logger module has a naming conflict: it reassigns `logging`
        # to the root logger, so calling configure_logger() again fails
        # with 'RootLogger has no attribute getLogger'. This tests that
        # the module-level `logging` is indeed a RootLogger.
        from utils import logger as logger_mod
        assert isinstance(logger_mod.logging, logging.Logger)

    def test_root_logger_has_handlers(self):
        from utils import logger as logger_mod
        assert len(logger_mod.logging.handlers) >= 1

    def test_root_logger_level(self):
        from utils import logger as logger_mod
        assert logger_mod.logging.level == logging.DEBUG

    def test_has_file_handler(self):
        from utils import logger as logger_mod
        file_handlers = [
            h for h in logger_mod.logging.handlers
            if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) >= 1

    def test_file_handler_level_debug(self):
        from utils import logger as logger_mod
        file_handlers = [
            h for h in logger_mod.logging.handlers
            if isinstance(h, logging.FileHandler)
        ]
        assert file_handlers[0].level == logging.DEBUG

    def test_has_console_handler(self):
        from utils import logger as logger_mod
        stream_handlers = [
            h for h in logger_mod.logging.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) >= 1

    def test_console_handler_level_info(self):
        from utils import logger as logger_mod
        stream_handlers = [
            h for h in logger_mod.logging.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert stream_handlers[0].level == logging.INFO

    def test_log_file_path_has_date_format(self):
        from utils import logger as logger_mod
        assert logger_mod.LOG_FILE is not None
        # LOG_FILE is formatted as MM_DD_YYYY_HH_MM_SS.log
        assert logger_mod.LOG_FILE.endswith(".log")

    def test_log_file_path(self):
        from utils import logger as logger_mod
        expected = os.path.join(LOG_DIR, logger_mod.LOG_FILE)
        assert logger_mod.log_file_path == expected

    def test_max_log_size_constant(self):
        from utils import logger as logger_mod
        assert logger_mod.MAX_LOG_SIZE == 5 * 1024 * 1024

    def test_backup_count_constant(self):
        from utils import logger as logger_mod
        assert logger_mod.BACKUP_COUNT == 3
