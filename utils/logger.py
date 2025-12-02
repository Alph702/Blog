import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from typing import Optional


def setup_logging(
    app: Optional[Flask] = None,
    log_file: Optional[str] = "app.log",
    level: int = logging.INFO,
):
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

    if getattr(target_logger, "_setup_logging_done", False):
        return target_logger
    setattr(target_logger, "_setup_logging_done", True)

    target_logger.setLevel(level)

    # Set root logger to WARNING by default to suppress external library logs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    for handler in list(target_logger.handlers):
        target_logger.removeHandler(handler)

    # 1. Console Handler: Outputs logs to stderr
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "{%(asctime)s} - [%(levelname)s] in %(module)s - (%(name)s) -- [%(filename)s::%(funcName)s:%(lineno)d]: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)  # Set handler level to capture our logs
    target_logger.addHandler(console_handler)

    # Also add handlers to root logger so app module loggers propagate correctly
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)

    file_path = ""
    # 2. File Handler: Outputs logs to a rotating file
    if log_file:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, log_file)

        # RotatingFileHandler: rotates log files after a certain size
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=1024 * 1024 * 10,  # 10 MB per log file
            backupCount=5,  # Keep up to 5 backup log files
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "{%(asctime)s} - [%(levelname)s] in %(module)s - (%(name)s) -- [%(filename)s::%(funcName)s:%(lineno)d]: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)  # Set handler level to capture our logs
        target_logger.addHandler(file_handler)

        # Also add file handler to root logger
        root_logger.addHandler(file_handler)

    app_loggers = [
        "auth",
        "blog",
        "admin",
        "api",
        "blueprints",
        "auth.blueprints",
        "auth.service",
        "auth.repository",
        "blog.blueprints",
        "admin.blueprints",
        "api.blueprints",
        "repositories",
        "post.repository",
        "video.repository",
        "post.service",
        "video.service",
        "auth.service",
        "worker.service",
        "services",
        "app",
        "config",
        "container",
        "worker",
    ]
    for logger_name in app_loggers:
        logging.getLogger(logger_name).setLevel(level)

    # Suppress verbose loggers from external libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    target_logger.info(f"Logging configured with level: {logging.getLevelName(level)}")
    if log_file:
        target_logger.info(f"Logs will also be written to: {file_path}")

    return target_logger
