# -*- coding: utf-8 -*-
"""
Data Cleaner - Handles DataFrame cleaning and preprocessing
"""
import pandas as pd
import numpy as np
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans and preprocesses DataFrame for analysis"""
    
    def __init__(self):
        self.max_comment_length = 2000  # Token limit consideration
        self.min_comment_length = 5     # Minimum meaningful comment length
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main cleaning pipeline"""
        if df.empty:
            logger.warning("Empty DataFrame provided to cleaner")
            return df
        
        logger.info(f"Starting data cleaning. Initial shape: {df.shape}")
        
        # Create a copy to avoid modifying original
        df_clean = df.copy()
        
        # Step 1: Clean column names
        df_clean = self._clean_column_names(df_clean)
        
        # Step 2: Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Step 3: Clean comments
        df_clean = self._clean_comments(df_clean)
        
        # Step 4: Clean NPS scores
        df_clean = self._clean_nps_scores(df_clean)
        
        # Step 5: Clean ratings (Nota column)
        df_clean = self._clean_ratings(df_clean)
        
        # Step 6: Remove invalid rows
        df_clean = self._remove_invalid_rows(df_clean)
        
        logger.info(f"Data cleaning completed. Final shape: {df_clean.shape}")
        logger.info(f"Rows removed: {len(df) - len(df_clean)}")
        
        return df_clean
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean column names - remove extra spaces, standardize"""
        df.columns = df.columns.str.strip()
        
        # Map common column name variations to standard names
        column_mapping = {
            'nps': 'NPS',
            'score': 'NPS', 
            'rating': 'Nota',
            'nota': 'Nota',
            'calificacion': 'Nota',
            'comment': 'Comentario Final',
            'comentario': 'Comentario Final',
            'feedback': 'Comentario Final'
        }
        
        for old_name, new_name in column_mapping.items():
            df.columns = df.columns.str.replace(old_name, new_name, case=False)
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately for each column type"""
        
        # For comments: drop rows with missing comments
        if 'Comentario Final' in df.columns:
            initial_count = len(df)
            df = df.dropna(subset=['Comentario Final'])
            dropped_count = initial_count - len(df)
            if dropped_count > 0:
                logger.info(f"Removed {dropped_count} rows with missing comments")
        
        # For NPS: convert to numeric, handle invalid values
        if 'NPS' in df.columns:
            df['NPS'] = pd.to_numeric(df['NPS'], errors='coerce')
            # Don't drop NPS nulls here - handle in validation
        
        # For Nota: convert to numeric
        if 'Nota' in df.columns:
            df['Nota'] = pd.to_numeric(df['Nota'], errors='coerce')
        
        return df
    
    def _clean_comments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean comment text"""
        if 'Comentario Final' not in df.columns:
            return df
        
        def clean_comment_text(text):
            if pd.isna(text) or not isinstance(text, str):
                return ""
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters that might cause issues
            text = re.sub(r'[^\w\s.,!?¿¡()-]', '', text)
            
            # Truncate if too long (to respect token limits)
            if len(text) > self.max_comment_length:
                text = text[:self.max_comment_length].rsplit(' ', 1)[0] + "..."
                logger.debug(f"Truncated long comment to {len(text)} characters")
            
            return text
        
        df['Comentario Final'] = df['Comentario Final'].apply(clean_comment_text)
        
        # Log cleaning statistics
        too_short = (df['Comentario Final'].str.len() < self.min_comment_length).sum()
        if too_short > 0:
            logger.info(f"Found {too_short} comments shorter than {self.min_comment_length} characters")
        
        return df
    
    def _clean_nps_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate NPS scores"""
        if 'NPS' not in df.columns:
            return df
        
        initial_count = len(df)
        
        # Ensure NPS scores are in valid range (0-10)
        df['NPS'] = df['NPS'].apply(lambda x: x if pd.isna(x) or (0 <= x <= 10) else np.nan)
        
        invalid_nps = df['NPS'].isna().sum()
        if invalid_nps > 0:
            logger.info(f"Found {invalid_nps} invalid NPS scores (outside 0-10 range)")
        
        return df
    
    def _clean_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean rating scores (Nota column)"""
        if 'Nota' not in df.columns:
            return df
        
        # Assume ratings are on a scale (could be 1-5, 1-10, etc.)
        # For now, just ensure they're positive numbers
        df.loc[df['Nota'] < 0, 'Nota'] = np.nan
        
        invalid_ratings = df['Nota'].isna().sum()
        if invalid_ratings > 0:
            logger.info(f"Found {invalid_ratings} invalid ratings")
        
        return df
    
    def _remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that don't meet minimum quality requirements"""
        initial_count = len(df)
        
        # Remove rows with comments that are too short
        if 'Comentario Final' in df.columns:
            df = df[df['Comentario Final'].str.len() >= self.min_comment_length]
        
        # Remove rows where comment is just whitespace or special characters
        if 'Comentario Final' in df.columns:
            df = df[df['Comentario Final'].str.strip() != ""]
            # Remove comments that are just numbers or special characters
            df = df[df['Comentario Final'].str.contains(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', regex=True)]
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} invalid rows during final cleanup")
        
        return df
    
    def get_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> dict:
        """Generate a report of cleaning operations"""
        return {
            'original_rows': len(original_df),
            'cleaned_rows': len(cleaned_df),
            'rows_removed': len(original_df) - len(cleaned_df),
            'removal_percentage': round(((len(original_df) - len(cleaned_df)) / len(original_df)) * 100, 2),
            'columns_before': list(original_df.columns),
            'columns_after': list(cleaned_df.columns),
            'missing_values_after': cleaned_df.isnull().sum().to_dict(),
            'comment_length_stats': {
                'min': cleaned_df['Comentario Final'].str.len().min() if 'Comentario Final' in cleaned_df.columns else 0,
                'max': cleaned_df['Comentario Final'].str.len().max() if 'Comentario Final' in cleaned_df.columns else 0,
                'avg': round(cleaned_df['Comentario Final'].str.len().mean(), 1) if 'Comentario Final' in cleaned_df.columns else 0
            }
        }

# Global instance for easy import
cleaner = DataCleaner()

# Convenience function
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience function to clean DataFrame"""
    return cleaner.clean(df)