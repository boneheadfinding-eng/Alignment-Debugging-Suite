"""
Logging utilities for the alignment debugging suite.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.
    
    Args:
        name: Logger name
        level: Logging level (defaults to INFO)
        log_file: Path to log file (optional)
        console: Whether to log to console
        json_format: Use JSON format for logs
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level or 'INFO')
    logger.setLevel(log_level)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if json_format:
            console_formatter = JSONFormatter()
        else:
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if needed
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class LogContext:
    """Context manager for adding extra data to logs."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra_data = kwargs
        self.old_factory = None
        
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_data = self.extra_data
            return record
            
        logging.setLogRecordFactory(record_factory)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


class MetricsLogger:
    """Logger specifically for metrics and performance data."""
    
    def __init__(self, name: str, metrics_file: str):
        self.logger = setup_logger(
            f"{name}_metrics",
            level='INFO',
            log_file=metrics_file,
            console=False,
            json_format=True
        )
        
    def log_metric(self, metric_name: str, value: float, **tags):
        """Log a metric with optional tags."""
        self.logger.info(
            f"METRIC: {metric_name}",
            extra={'metric_name': metric_name, 'value': value, 'tags': tags}
        )
        
    def log_timing(self, operation: str, duration: float, **tags):
        """Log timing information."""
        self.log_metric(f"{operation}_duration", duration, **tags)
        
    def log_counter(self, counter_name: str, increment: int = 1, **tags):
        """Log a counter increment."""
        self.log_metric(f"{counter_name}_count", increment, **tags)


# Global logger instance
logger = setup_logger('ai_alignment_suite')