"""
Data Normalizer - Handles text normalization and standardization
"""
import pandas as pd
import re
import unicodedata
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DataNormalizer:
    """Normalizes text data for consistent processing"""
    
    def __init__(self):
        self.preserve_accents = True  # Keep Spanish accents
        self.normalize_whitespace = True
        self.remove_html = True
        self.standardize_encoding = True
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main normalization pipeline"""
        if df.empty:
            logger.warning("Empty DataFrame provided to normalizer")
            return df
        
        logger.info(f"Starting normalization for DataFrame with shape: {df.shape}")
        
        df_normalized = df.copy()
        
        # Normalize comments
        if 'Comentario Final' in df_normalized.columns:
            df_normalized['Comentario Final'] = df_normalized['Comentario Final'].apply(
                self._normalize_text
            )
        
        # Normalize other text columns if present
        text_columns = df_normalized.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col != 'Comentario Final' and df_normalized[col].dtype == 'object':
                # Only normalize if column contains text (not just numbers as strings)
                if df_normalized[col].astype(str).str.contains(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]').any():
                    df_normalized[col] = df_normalized[col].apply(self._normalize_text_light)
        
        logger.info("Normalization completed")
        return df_normalized
    
    def _normalize_text(self, text: Any) -> str:
        """Comprehensive text normalization for comments"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Step 1: Handle encoding issues
        if self.standardize_encoding:
            text = self._fix_encoding(text)
        
        # Step 2: Remove HTML tags if present
        if self.remove_html:
            text = self._remove_html_tags(text)
        
        # Step 3: Normalize Unicode
        text = self._normalize_unicode(text)
        
        # Step 4: Normalize whitespace
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # Step 5: Fix common text issues
        text = self._fix_common_issues(text)
        
        # Step 6: Standardize punctuation
        text = self._standardize_punctuation(text)
        
        return text.strip()
    
    def _normalize_text_light(self, text: Any) -> str:
        """Light normalization for non-comment text columns"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Just basic cleanup for non-comment columns
        text = self._normalize_whitespace(text)
        text = self._fix_encoding(text)
        
        return text.strip()
    
    def _fix_encoding(self, text: str) -> str:
        """Fix common encoding issues"""
        # Common encoding fixes for Spanish text
        encoding_fixes = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã‡': 'Ç', 'â€œ': '"', 'â€?': '"', 'â€™': "'",
            'â€"': '—', 'â€"': '–', 'Â´': "'", 'Â¿': '¿', 'Â¡': '¡'
        }
        
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags and entities"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove HTML entities
        html_entities = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
            '&apos;': "'", '&nbsp;': ' ', '&copy;': '©', '&reg;': '®'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters"""
        if self.preserve_accents:
            # Normalize to NFC form (composed characters)
            text = unicodedata.normalize('NFC', text)
        else:
            # Remove accents by decomposing and filtering
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize all types of whitespace"""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace non-breaking spaces and other space characters
        text = text.replace('\u00A0', ' ')  # Non-breaking space
        text = text.replace('\u2009', ' ')  # Thin space
        text = text.replace('\u200A', ' ')  # Hair space
        text = text.replace('\u2007', ' ')  # Figure space
        text = text.replace('\u2008', ' ')  # Punctuation space
        
        return text
    
    def _fix_common_issues(self, text: str) -> str:
        """Fix common text issues in Spanish comments"""
        # Fix repeated punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*([a-zA-ZáéíóúÁÉÍÓÚñÑ])', r'\1 \2', text)  # Add space after sentence end
        
        # Fix common Spanish contractions and issues
        text = re.sub(r'\bq\b', 'que', text, flags=re.IGNORECASE)  # "q" -> "que"
        text = re.sub(r'\bx\b', 'por', text, flags=re.IGNORECASE)  # "x" -> "por"
        text = re.sub(r'\bk\b', 'que', text, flags=re.IGNORECASE)  # "k" -> "que"
        
        # Fix repeated characters (but preserve Spanish "ll", "rr")
        text = re.sub(r'([^lr])\1{2,}', r'\1\1', text)  # Reduce repeated chars (except l,r)
        
        return text
    
    def _standardize_punctuation(self, text: str) -> str:
        """Standardize punctuation marks"""
        # Standardize quotation marks
        text = re.sub(r'[""„"]', '"', text)
        text = re.sub(r'[''‚']', "'", text)
        
        # Standardize dashes
        text = re.sub(r'[—–]', '-', text)
        
        # Standardize ellipsis
        text = re.sub(r'\.{3,}', '...', text)
        
        return text
    
    def get_normalization_stats(self, original_text: str, normalized_text: str) -> Dict[str, Any]:
        """Get statistics about normalization changes"""
        return {
            'original_length': len(original_text),
            'normalized_length': len(normalized_text),
            'length_change': len(normalized_text) - len(original_text),
            'character_changes': sum(1 for a, b in zip(original_text, normalized_text) if a != b),
            'html_tags_removed': len(re.findall(r'<[^>]+>', original_text)),
            'whitespace_normalized': len(re.findall(r'\s{2,}', original_text)) > 0
        }
    
    def batch_normalize_with_stats(self, texts: pd.Series) -> Dict[str, Any]:
        """Normalize a batch of texts and return statistics"""
        if texts.empty:
            return {'normalized_texts': texts, 'stats': {}}
        
        normalized_texts = texts.apply(self._normalize_text)
        
        # Calculate batch statistics
        total_texts = len(texts)
        changed_texts = sum(1 for orig, norm in zip(texts, normalized_texts) if orig != norm)
        
        avg_length_before = texts.str.len().mean()
        avg_length_after = normalized_texts.str.len().mean()
        
        stats = {
            'total_texts': total_texts,
            'texts_changed': changed_texts,
            'change_percentage': round((changed_texts / total_texts) * 100, 1),
            'avg_length_before': round(avg_length_before, 1),
            'avg_length_after': round(avg_length_after, 1),
            'length_change_avg': round(avg_length_after - avg_length_before, 1)
        }
        
        return {
            'normalized_texts': normalized_texts,
            'stats': stats
        }

# Global instance for easy import
normalizer = DataNormalizer()

# Convenience function
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience function to normalize DataFrame"""
    return normalizer.normalize(df)

def normalize_text(text: str) -> str:
    """Convenience function to normalize single text"""
    return normalizer._normalize_text(text)