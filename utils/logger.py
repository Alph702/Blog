import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from typing import Optional

def setup_logging(app: Optional[Flask] = None, log_file: Optional[str] = "app.log", level: int = logging.INFO):
    """
    Sets up the logging configuration for the application.

    This function configures both console and file logging. For Flask applications,
    it integrates with the app.logger instance. For other scripts or modules,
    it configures the root logger or a named logger.

    Args:
        app: The Flask application instance (optional). If provided, app.logger is configured.
        log_file: The base name of the log file (e.g., "app.log").
        level: The minimum logging level to capture (e.g., logging.INFO, logging.DEBUG).
    """
    if app:
        target_logger = app.logger
    else:
        target_logger = logging.getLogger()

    target_logger.setLevel(level)

    for handler in list(target_logger.handlers):
        target_logger.removeHandler(handler)

    # 1. Console Handler: Outputs logs to stderr
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    target_logger.addHandler(console_handler)

    file_path = ""
    # 2. File Handler: Outputs logs to a rotating file
    if log_file:
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, log_file)

        # RotatingFileHandler: rotates log files after a certain size
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=1024 * 1024 * 10,  # 10 MB per log file
            backupCount=5,              # Keep up to 5 backup log files
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        target_logger.addHandler(file_handler)

    # Suppress verbose loggers from external libraries if not in DEBUG mode
    if level > logging.DEBUG:
        logging.getLogger('werkzeug').setLevel(logging.WARNING) # Flask's internal web server
        logging.getLogger('supabase').setLevel(logging.WARNING) # Supabase client library

    target_logger.info(f"Logging configured with level: {logging.getLevelName(level)}")
    if log_file:
        target_logger.info(f"Logs will also be written to: {file_path}")

    return target_logger