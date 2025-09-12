"""
Excel File Reader - Handles Excel file parsing and initial data loading
"""
import pandas as pd
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExcelReader:
    """Reads Excel files and converts to DataFrame"""
    
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls', '.csv']
        self.required_columns = ['NPS', 'Nota', 'Comentario Final']
    
    def read_excel(self, file_path: str) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        if not file_path:
            raise ValueError("File path cannot be empty")
        
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path_obj.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {path_obj.suffix}")
        
        try:
            # Read based on file extension
            if path_obj.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
            
            logger.info(f"Successfully read file: {file_path}")
            logger.info(f"Shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise ValueError(f"Could not read file: {e}")
    
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Validate that required columns exist in DataFrame"""
        missing_columns = []
        
        for required_col in self.required_columns:
            if required_col not in df.columns:
                missing_columns.append(required_col)
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            logger.info(f"Available columns: {list(df.columns)}")
            return False
        
        return True
    
    def get_file_info(self, file_path: str) -> dict:
        """Get basic information about the file"""
        try:
            path_obj = Path(file_path)
            df = self.read_excel(file_path)
            
            return {
                'filename': path_obj.name,
                'size_mb': round(path_obj.stat().st_size / (1024 * 1024), 2),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'has_required_columns': self.validate_columns(df),
                'missing_columns': [col for col in self.required_columns if col not in df.columns]
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {'error': str(e)}
    
    def preview_data(self, file_path: str, num_rows: int = 5) -> pd.DataFrame:
        """Get a preview of the data"""
        df = self.read_excel(file_path)
        return df.head(num_rows)

# Global instance for easy import
reader = ExcelReader()

# Convenience functions
def read_excel(file_path: str) -> pd.DataFrame:
    """Convenience function to read Excel file"""
    return reader.read_excel(file_path)

def validate_file(file_path: str) -> bool:
    """Convenience function to validate file format and columns"""
    try:
        df = reader.read_excel(file_path)
        return reader.validate_columns(df)
    except Exception:
        return False

def get_file_preview(file_path: str, rows: int = 5) -> pd.DataFrame:
    """Convenience function to get file preview"""
    return reader.preview_data(file_path, rows)