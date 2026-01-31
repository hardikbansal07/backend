import logging
import sys
import os

def setup_logger(name, console_level=logging.INFO):
    """
    Setup logger with environment-aware configuration.
    
    Production Mode (ENVIRONMENT=production):
    - No file logging
    - Only WARNING and above to console
    
    Development Mode (default):
    - Full DEBUG logging to file
    - INFO and above to console
    
    Args:
        name: Logger name
        console_level: Logging level for console output (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Check environment
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    is_production = environment == 'production'
    
    if is_production:
        # Production: Minimal logging
        logger.setLevel(logging.WARNING)
        
        # Only console handler with WARNING level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('%(levelname)s - %(name)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    else:
        # Development: Full logging
        logger.setLevel(logging.DEBUG)
        
        # File handler - captures everything (DEBUG and above)
        file_handler = logging.FileHandler('astro_pipeline.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler - shows INFO and above (less verbose)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter('%(levelname)s - %(name)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger
