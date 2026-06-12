from __future__ import annotations

import logging


class CaptureLog(logging.Handler):
    """Context manager to capture log entries.

    Usage::

      with CaptureLog('foo', logging.DEBUG) as captured:
          logger = logging.getLogger('foo')
          logger.debug("Debug")

      >>> captured.records[0].getMessage()
      'Debug'

    :param logger_name: the name of the logger, can be prefix too.
    :param level: the loglevel to capture at, only log entries equal or
      higher than this level are captured.
    """

    def __init__(self, logger_name: str, level: int = logging.WARNING):
        super().__init__(level)
        self.logger_name = logger_name
        self.level = level
        self.records: list[logging.LogRecord] = []
        """Logging records captured.
        """

    @property
    def record_tuples(self) -> list[tuple[str, int, str]]:
        """Returns list of log entries in tuple form.

        The format of the tuple is ``(logger_name, log_level, message)``
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records]

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def __enter__(self) -> CaptureLog:
        self.records = []
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self)
        logger.setLevel(self.level)
        return self

    def __exit__(self, type: object, value: object, traceback: object) -> None:
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self)
        logger.setLevel(logging.NOTSET)
