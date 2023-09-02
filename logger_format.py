import os
import logging
from pathlib import Path

log_levels_dict = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

path_level = 2


def get_logger(
    get_name, file_name=None, logging_level="info", clear_previous_logs=False
):
    logger = logging.getLogger(get_name)

    if len(logger.handlers) == 0:
        if file_name is not None:
            if clear_previous_logs and os.path.exists(file_name):
                os.remove(file_name)
            file_handler = logging.FileHandler(file_name)
            file_handler.setFormatter(PlainFormatter())
            logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(ColorFormatter())
        logger.addHandler(stream_handler)

    logger.setLevel(log_levels_dict[logging_level.lower()])

    return logger


class ColorFormatter(logging.Formatter):
    def format(self, record):
        record.shortpath = path_to_relative_directories(record.pathname, path_level)
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        else:
            color = {
                logging.WARNING: 33,
                logging.ERROR: 31,
                logging.FATAL: 31,
                logging.DEBUG: 36,
            }.get(record.levelno, 0)
            level_style = (
                f"\033[1m\033[{color}m%(levelname)s:%(asctime)s:"
                + "%(shortpath)s\033[0m"
            )
            self._style._fmt = level_style + ": %(message)s"

        return super().format(record)


class PlainFormatter(logging.Formatter):
    def format(self, record):
        record.shortpath = path_to_relative_directories(record.pathname, path_level)
        if record.levelno == logging.INFO:
            self._style._fmt = "%(asctime)s: %(message)s"
        else:
            level_style = "%(levelname)s:%(asctime)s:%(shortpath)s: %(message)s"
            self._style._fmt = level_style + ": %(message)s"

        return super().format(record)


def path_to_relative_directories(pathname, num_dirs):
    return Path(*Path(pathname).parts[-num_dirs - 1 :])


if __name__ == "__main__":
    pass
