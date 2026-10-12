"""
Logging utility module for the bot
Provides consistent, timestamped logging with color codes and log levels
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color codes for different log levels"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the message
        return super().format(record)


def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Setup a logger with consistent formatting

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Format: [TIMESTAMP] [LEVEL] [MODULE] Message
    console_format = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))

        # File format without colors
        file_format = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# Convenience function for quick logging
def log_message(level: str, message: str, module: str = "BOT"):
    """
    Quick log message without setting up a logger

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Message to log
        module: Module name for identification
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] [{module}] {message}")


# Create default logger for the bot
bot_logger = setup_logger(
    name="TradingVaultBot",
    log_file="logs/bot.log",
    level="INFO"
)

# Create logger for payment system
payment_logger = setup_logger(
    name="PaymentSystem",
    log_file="logs/payments.log",
    level="INFO"
)

# Create logger for Gmail API
gmail_logger = setup_logger(
    name="GmailAPI",
    log_file="logs/gmail.log",
    level="INFO"
)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for a specific module

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logger(
        name=name,
        log_file=f"logs/{name.lower()}.log",
        level="INFO"
    )
