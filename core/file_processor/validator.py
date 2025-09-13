# -*- coding: utf-8 -*-
"""
Data Validator - Validates DataFrame structure and content quality
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates DataFrame structure and data quality"""
    
    def __init__(self):
        self.required_columns = ['NPS', 'Nota', 'Comentario Final']
        self.min_rows = 1
        self.max_rows = 50000  # Performance consideration
        self.min_comment_length = 5
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main validation pipeline - raises exceptions for critical issues"""
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        logger.info(f"Starting validation for DataFrame with shape: {df.shape}")
        
        # Critical validations (will raise exceptions)
        self._validate_structure(df)
        self._validate_size(df)
        
        # Quality validations (will log warnings but continue)
        validation_report = self._validate_data_quality(df)
        
        if validation_report['errors']:
            logger.error("Data quality issues found:")
            for error in validation_report['errors']:
                logger.error(f"  - {error}")
        
        if validation_report['warnings']:
            logger.warning("Data quality warnings:")
            for warning in validation_report['warnings']:
                logger.warning(f"  - {warning}")
        
        logger.info("Validation completed")
        return df
    
    def _validate_structure(self, df: pd.DataFrame):
        """Validate DataFrame has required columns"""
        missing_columns = []
        for col in self.required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns: {available_cols}"
            )
        
        logger.info("[OK] All required columns present")
    
    def _validate_size(self, df: pd.DataFrame):
        """Validate DataFrame size is within acceptable limits"""
        if len(df) < self.min_rows:
            raise ValueError(f"DataFrame too small: {len(df)} rows. Minimum: {self.min_rows}")
        
        if len(df) > self.max_rows:
            raise ValueError(f"DataFrame too large: {len(df)} rows. Maximum: {self.max_rows}")
        
        logger.info(f"[OK] DataFrame size acceptable: {len(df)} rows")
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Validate data quality and return report"""
        errors = []
        warnings = []
        
        # Validate NPS scores
        nps_issues = self._validate_nps_column(df)
        errors.extend(nps_issues['errors'])
        warnings.extend(nps_issues['warnings'])
        
        # Validate ratings
        rating_issues = self._validate_rating_column(df)
        warnings.extend(rating_issues['warnings'])
        
        # Validate comments
        comment_issues = self._validate_comment_column(df)
        errors.extend(comment_issues['errors'])
        warnings.extend(comment_issues['warnings'])
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_nps_column(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Validate NPS column"""
        errors = []
        warnings = []
        
        if 'NPS' not in df.columns:
            return {'errors': errors, 'warnings': warnings}
        
        # Check for missing values
        missing_nps = df['NPS'].isna().sum()
        if missing_nps > 0:
            missing_pct = (missing_nps / len(df)) * 100
            if missing_pct == 100:
                errors.append(f"All NPS values are missing ({missing_nps} rows). Check if your Excel has NPS data in the correct column or contains non-numeric values.")
            elif missing_pct > 50:
                errors.append(f"Too many missing NPS values: {missing_nps} ({missing_pct:.1f}%)")
            else:
                warnings.append(f"Missing NPS values: {missing_nps} ({missing_pct:.1f}%)")
        
        # Check for invalid ranges
        valid_nps = df['NPS'].dropna()
        if len(valid_nps) > 0:
            invalid_range = ((valid_nps < 0) | (valid_nps > 10)).sum()
            if invalid_range > 0:
                errors.append(f"NPS values outside 0-10 range: {invalid_range}")
            
            # Check distribution
            unique_values = sorted(valid_nps.unique())
            if len(unique_values) < 3:
                warnings.append(f"Low NPS score diversity: only {len(unique_values)} unique values")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_rating_column(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Validate rating column (Nota)"""
        warnings = []
        
        if 'Nota' not in df.columns:
            return {'warnings': warnings}
        
        # Check for missing values
        missing_ratings = df['Nota'].isna().sum()
        if missing_ratings > 0:
            missing_pct = (missing_ratings / len(df)) * 100
            if missing_pct > 30:
                warnings.append(f"Many missing rating values: {missing_ratings} ({missing_pct:.1f}%)")
        
        # Check for negative values
        valid_ratings = df['Nota'].dropna()
        if len(valid_ratings) > 0:
            negative_ratings = (valid_ratings < 0).sum()
            if negative_ratings > 0:
                warnings.append(f"Negative rating values found: {negative_ratings}")
        
        return {'warnings': warnings}
    
    def _validate_comment_column(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Validate comments column"""
        errors = []
        warnings = []
        
        if 'Comentario Final' not in df.columns:
            return {'errors': errors, 'warnings': warnings}
        
        # Check for missing comments
        missing_comments = df['Comentario Final'].isna().sum()
        if missing_comments > 0:
            missing_pct = (missing_comments / len(df)) * 100
            if missing_pct > 10:
                errors.append(f"Too many missing comments: {missing_comments} ({missing_pct:.1f}%)")
            else:
                warnings.append(f"Missing comments: {missing_comments} ({missing_pct:.1f}%)")
        
        # Check comment quality
        valid_comments = df['Comentario Final'].dropna()
        if len(valid_comments) > 0:
            # Check for very short comments
            short_comments = (valid_comments.str.len() < self.min_comment_length).sum()
            if short_comments > 0:
                short_pct = (short_comments / len(valid_comments)) * 100
                warnings.append(f"Very short comments: {short_comments} ({short_pct:.1f}%)")
            
            # Check for very long comments
            long_comments = (valid_comments.str.len() > 1000).sum()
            if long_comments > 0:
                warnings.append(f"Very long comments: {long_comments} (may be truncated)")
            
            # Check for duplicate comments
            duplicate_comments = valid_comments.duplicated().sum()
            if duplicate_comments > 0:
                dup_pct = (duplicate_comments / len(valid_comments)) * 100
                if dup_pct > 5:
                    warnings.append(f"Many duplicate comments: {duplicate_comments} ({dup_pct:.1f}%) - consider reviewing data quality")
                else:
                    warnings.append(f"Duplicate comments found: {duplicate_comments} ({dup_pct:.1f}%) - this is common in survey data")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data profile"""
        profile = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
        
        # NPS analysis
        if 'NPS' in df.columns:
            nps_stats = df['NPS'].describe().to_dict()
            nps_stats['unique_values'] = df['NPS'].nunique()
            nps_stats['value_counts'] = df['NPS'].value_counts().to_dict()
            profile['nps_analysis'] = nps_stats
        
        # Comment analysis
        if 'Comentario Final' in df.columns:
            comments = df['Comentario Final'].dropna()
            if len(comments) > 0:
                profile['comment_analysis'] = {
                    'total_comments': len(comments),
                    'avg_length': round(comments.str.len().mean(), 1),
                    'min_length': comments.str.len().min(),
                    'max_length': comments.str.len().max(),
                    'empty_comments': (comments.str.strip() == '').sum(),
                    'duplicates': comments.duplicated().sum(),
                    'languages_detected': self._detect_languages_sample(comments)
                }
        
        return profile
    
    def _detect_languages_sample(self, comments: pd.Series, sample_size: int = 100) -> List[str]:
        """Detect languages in a sample of comments"""
        # Simple language detection based on common Spanish words
        spanish_indicators = ['el', 'la', 'es', 'en', 'de', 'que', 'y', 'se', 'no', 'un', 'por', 'con']
        
        sample = comments.sample(min(sample_size, len(comments)))
        languages = []
        
        spanish_count = 0
        for comment in sample:
            if isinstance(comment, str):
                comment_lower = comment.lower()
                spanish_words = sum(1 for word in spanish_indicators if word in comment_lower)
                if spanish_words >= 2:
                    spanish_count += 1
        
        if spanish_count / len(sample) > 0.7:
            languages.append('Spanish')
        else:
            languages.append('Mixed/Other')
        
        return languages

# Global instance for easy import
validator = DataValidator()

# Convenience function
def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience function to validate DataFrame"""
    return validator.validate(df)

def get_validation_report(df: pd.DataFrame) -> dict:
    """Get comprehensive validation report"""
    try:
        validator.validate(df)
        return {
            'valid': True,
            'profile': validator.get_data_profile(df),
            'errors': [],
            'warnings': []
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'profile': None
        }