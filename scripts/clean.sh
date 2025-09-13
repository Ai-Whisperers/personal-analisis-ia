#!/bin/bash
# CLEAN.SH - Deep Python Cache Cleanup Script
# Removes ALL Python cache files from EVERY level of directories

echo "🧹 STARTING DEEP PYTHON CACHE CLEANUP"
echo "========================================"

# Get current directory for reference
CURRENT_DIR=$(pwd)
echo "📂 Working directory: $CURRENT_DIR"

echo ""
echo "🔍 Scanning for Python cache directories..."
PYCACHE_COUNT=$(find . -type d -name "__pycache__" | wc -l)
echo "   Found $PYCACHE_COUNT __pycache__ directories"

echo ""
echo "🔍 Scanning for .pyc files..."
PYC_COUNT=$(find . -name "*.pyc" | wc -l)
echo "   Found $PYC_COUNT .pyc files"

echo ""
echo "🔍 Scanning for .pyo files..."
PYO_COUNT=$(find . -name "*.pyo" | wc -l)
echo "   Found $PYO_COUNT .pyo files"

echo ""
echo "🗑️  REMOVING ALL PYTHON CACHE FILES..."
echo "----------------------------------------"

# Remove __pycache__ directories (all levels)
echo "🗂️  Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files (all levels) 
echo "🧹 Removing .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files (all levels)
echo "🧹 Removing .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove .pyd files (Windows compiled extensions)
echo "🧹 Removing .pyd files..."
find . -name "*.pyd" -delete 2>/dev/null || true

# Remove pytest cache
echo "🧪 Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove mypy cache
echo "🔍 Removing mypy cache..."
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove coverage cache
echo "📊 Removing coverage cache..."
find . -name ".coverage" -delete 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# Remove Streamlit cache
echo "🎭 Removing Streamlit cache..."
find . -type d -name ".streamlit" -path "*/cache/*" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "✅ CLEANUP COMPLETED!"
echo "===================="

# Verify cleanup
echo ""
echo "🔍 VERIFICATION:"
REMAINING_PYCACHE=$(find . -type d -name "__pycache__" | wc -l)
REMAINING_PYC=$(find . -name "*.pyc" | wc -l)
REMAINING_PYO=$(find . -name "*.pyo" | wc -l)

echo "   Remaining __pycache__ directories: $REMAINING_PYCACHE"
echo "   Remaining .pyc files: $REMAINING_PYC"  
echo "   Remaining .pyo files: $REMAINING_PYO"

if [ $REMAINING_PYCACHE -eq 0 ] && [ $REMAINING_PYC -eq 0 ] && [ $REMAINING_PYO -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS: All Python cache files removed!"
    echo "💡 Now you can safely restart your Streamlit app:"
    echo "   streamlit run streamlit_app.py"
else
    echo ""
    echo "⚠️  WARNING: Some cache files may remain"
    echo "💡 Try running this script as administrator/sudo"
fi

echo ""
echo "🚀 READY FOR FRESH DEPLOYMENT!"