import logging
import logging.handlers

def configure_logging(log_path: str = None, verbose: bool = False):
    root_logger = logging.getLogger()

    # Clear any existing handlers to avoid duplicate logs
    root_logger.handlers = []

    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        root_logger.addHandler(stream_handler)

    if log_path:
        info_handler = logging.handlers.RotatingFileHandler(filename=f"{log_path}_training_log.txt")
        info_handler.setLevel(logging.INFO)
        root_logger.addHandler(info_handler)

    root_logger.setLevel(logging.INFO)