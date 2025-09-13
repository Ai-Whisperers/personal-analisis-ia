#!/bin/bash
# RESTART.SH - Complete application restart with cache cleanup

echo "🔄 COMPLETE APPLICATION RESTART"
echo "==============================="

# Step 1: Kill any running Streamlit processes
echo "🔪 Stopping Streamlit processes..."
pkill -f streamlit 2>/dev/null || echo "   No running Streamlit processes found"

# Step 2: Clean Python cache
echo ""
echo "🧹 Cleaning Python cache..."
./scripts/clean.sh

# Step 3: Wait a moment for processes to fully stop
echo ""
echo "⏳ Waiting for processes to stop..."
sleep 2

# Step 4: Test critical imports
echo ""
echo "🧪 Testing critical imports..."
python -c "
try:
    from utils.performance_monitor import monitor
    print('✅ PerformanceMonitor import: OK')
    
    # Test the actual usage
    with monitor('test_restart'):
        pass
    print('✅ PerformanceMonitor functionality: OK')
    
    from controller import PipelineController
    print('✅ PipelineController import: OK')
    
    print('✅ ALL CRITICAL IMPORTS: WORKING')
except Exception as e:
    print(f'❌ IMPORT ERROR: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Import tests failed - check your code"
    exit 1
fi

# Step 5: Start Streamlit
echo ""
echo "🚀 Starting Streamlit application..."
echo "   URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run streamlit_app.py