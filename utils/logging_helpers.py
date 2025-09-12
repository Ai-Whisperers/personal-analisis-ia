"""
Logging Helpers - Consistent logging configuration and utilities
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import json

class CustomFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'color') and record.color:
            log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class LoggingHelper:
    """Central logging configuration and utilities"""
    
    def __init__(self):
        self.log_dir = Path("local-reports/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.configured_loggers = set()
    
    def setup_logging(
        self,
        level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_filename: Optional[str] = None
    ) -> None:
        """Setup logging configuration"""
        
        # Convert string level to logging level
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            console_formatter = CustomFormatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            
            # Add color support
            if hasattr(console_handler.stream, 'isatty') and console_handler.stream.isatty():
                console_handler.addFilter(lambda record: setattr(record, 'color', True) or True)
            
            root_logger.addHandler(console_handler)
        
        # File handler
        if log_to_file:
            if not log_filename:
                log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
            
            log_file_path = self.log_dir / log_filename
            
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            file_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            root_logger.addHandler(file_handler)
        
        # Configure specific loggers
        self._configure_library_loggers()
        
        logging.info(f"Logging configured - Level: {level}, File: {log_to_file}, Console: {log_to_console}")
    
    def _configure_library_loggers(self):
        """Configure logging for third-party libraries"""
        
        # Reduce noise from third-party libraries
        library_configs = {
            'urllib3.connectionpool': logging.WARNING,
            'requests.packages.urllib3': logging.WARNING,
            'openai': logging.INFO,
            'matplotlib': logging.WARNING,
            'plotly': logging.WARNING,
            'streamlit': logging.WARNING
        }
        
        for logger_name, log_level in library_configs.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger instance"""
        logger = logging.getLogger(name)
        
        # Ensure logger inherits from root configuration
        if name not in self.configured_loggers:
            logger.setLevel(logging.NOTSET)  # Inherit from parent
            self.configured_loggers.add(name)
        
        return logger
    
    def log_function_call(
        self,
        logger: logging.Logger,
        func_name: str,
        args: tuple = None,
        kwargs: dict = None,
        level: str = "DEBUG"
    ):
        """Log function call with arguments"""
        log_level = getattr(logging, level.upper(), logging.DEBUG)
        
        if logger.isEnabledFor(log_level):
            call_info = f"Calling {func_name}"
            
            if args:
                args_str = ", ".join(str(arg)[:100] for arg in args)  # Limit arg string length
                call_info += f" with args: ({args_str})"
            
            if kwargs:
                kwargs_str = ", ".join(f"{k}={str(v)[:50]}" for k, v in kwargs.items())
                call_info += f" with kwargs: {{{kwargs_str}}}"
            
            logger.log(log_level, call_info)
    
    def log_performance_metrics(
        self,
        logger: logging.Logger,
        metrics: Dict[str, Any],
        level: str = "INFO"
    ):
        """Log performance metrics in structured format"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if logger.isEnabledFor(log_level):
            logger.log(log_level, f"Performance metrics: {json.dumps(metrics, indent=2)}")
    
    def log_data_info(
        self,
        logger: logging.Logger,
        data_name: str,
        data: Any,
        level: str = "INFO"
    ):
        """Log information about data structures"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if logger.isEnabledFor(log_level):
            info = {"data_name": data_name}
            
            try:
                import pandas as pd
                if isinstance(data, pd.DataFrame):
                    info.update({
                        "type": "DataFrame",
                        "shape": data.shape,
                        "columns": list(data.columns),
                        "dtypes": data.dtypes.to_dict(),
                        "memory_usage": f"{data.memory_usage(deep=True).sum() / 1024:.1f} KB"
                    })
                elif isinstance(data, (list, tuple)):
                    info.update({
                        "type": type(data).__name__,
                        "length": len(data),
                        "sample": str(data[:3]) if len(data) > 3 else str(data)
                    })
                elif isinstance(data, dict):
                    info.update({
                        "type": "dict",
                        "keys": list(data.keys()),
                        "length": len(data)
                    })
                else:
                    info.update({
                        "type": type(data).__name__,
                        "value": str(data)[:200]  # Limit string length
                    })
            
            except Exception as e:
                info["error_analyzing_data"] = str(e)
            
            logger.log(log_level, f"Data info: {json.dumps(info, indent=2, default=str)}")
    
    def log_error_context(
        self,
        logger: logging.Logger,
        error: Exception,
        context: Dict[str, Any] = None,
        include_traceback: bool = True
    ):
        """Log error with additional context"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        if include_traceback:
            import traceback
            error_info["traceback"] = traceback.format_exc()
        
        logger.error(f"Error occurred: {json.dumps(error_info, indent=2, default=str)}")
    
    def create_operation_logger(
        self,
        operation_name: str,
        log_level: str = "INFO"
    ):
        """Create a context manager for operation logging"""
        return OperationLogger(self.get_logger(f"operation.{operation_name}"), operation_name, log_level)

class OperationLogger:
    """Context manager for logging operations with timing"""
    
    def __init__(self, logger: logging.Logger, operation_name: str, log_level: str = "INFO"):
        self.logger = logger
        self.operation_name = operation_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        if self.logger.isEnabledFor(self.log_level):
            self.logger.log(self.log_level, f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        if exc_type is None:
            if self.logger.isEnabledFor(self.log_level):
                self.logger.log(
                    self.log_level,
                    f"Completed operation: {self.operation_name} in {duration.total_seconds():.3f}s"
                )
        else:
            self.logger.error(
                f"Failed operation: {self.operation_name} after {duration.total_seconds():.3f}s - "
                f"{exc_type.__name__}: {exc_val}"
            )
    
    def log(self, message: str, level: str = None):
        """Log a message within the operation context"""
        actual_level = getattr(logging, level.upper(), self.log_level) if level else self.log_level
        self.logger.log(actual_level, f"[{self.operation_name}] {message}")
    
    def log_progress(self, current: int, total: int, message: str = ""):
        """Log progress within the operation"""
        progress_pct = (current / total) * 100 if total > 0 else 0
        progress_msg = f"[{self.operation_name}] Progress: {current}/{total} ({progress_pct:.1f}%)"
        if message:
            progress_msg += f" - {message}"
        
        self.logger.log(self.log_level, progress_msg)

# Global logging helper instance
logging_helper = LoggingHelper()

# Convenience functions
def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_filename: Optional[str] = None
):
    """Setup application logging"""
    logging_helper.setup_logging(level, log_to_file, log_to_console, log_filename)

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger"""
    return logging_helper.get_logger(name)

def log_operation(operation_name: str, log_level: str = "INFO"):
    """Context manager for logging operations"""
    return logging_helper.create_operation_logger(operation_name, log_level)