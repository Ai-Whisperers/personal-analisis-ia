# -*- coding: utf-8 -*-
"""
File Processing Module for Excel I/O and Data Validation
Provides reader, cleaner, validator, and normalizer components
"""

# Import individual modules for compatibility with engine_controller
from . import reader
from . import cleaner
from . import validator
from . import normalizer

# Export main classes for direct import
from .reader import read_excel, validate_file
from .cleaner import DataCleaner, clean
from .validator import DataValidator, validate
from .normalizer import DataNormalizer, normalize

__all__ = [
    'reader', 'cleaner', 'validator', 'normalizer',
    'read_excel', 'validate_file', 'clean', 'validate', 'normalize',
    'DataCleaner', 'DataValidator', 'DataNormalizer'
]