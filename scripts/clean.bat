@echo off
REM CLEAN.BAT - Windows Python Cache Cleanup
REM Removes ALL Python cache files from EVERY level of directories

echo 🧹 STARTING DEEP PYTHON CACHE CLEANUP
echo ========================================

echo 📂 Working directory: %CD%

echo.
echo 🗑️  REMOVING ALL PYTHON CACHE FILES...
echo ----------------------------------------

REM Remove __pycache__ directories
echo 🗂️  Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Remove .pyc files
echo 🧹 Removing .pyc files...
del /s /q *.pyc >nul 2>&1

REM Remove .pyo files
echo 🧹 Removing .pyo files...
del /s /q *.pyo >nul 2>&1

REM Remove .pyd files (Windows compiled extensions)
echo 🧹 Removing .pyd files...
del /s /q *.pyd >nul 2>&1

REM Remove pytest cache
echo 🧪 Removing pytest cache...
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"

REM Remove mypy cache  
echo 🔍 Removing mypy cache...
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d"

REM Remove coverage files
echo 📊 Removing coverage cache...
del /s /q .coverage >nul 2>&1
for /d /r . %%d in (htmlcov) do @if exist "%%d" rd /s /q "%%d"

echo.
echo ✅ CLEANUP COMPLETED!
echo ====================

echo.
echo 🎉 SUCCESS: All Python cache files removed!
echo 💡 Now you can safely restart your Streamlit app:
echo    streamlit run streamlit_app.py

echo.
echo 🚀 READY FOR FRESH DEPLOYMENT!

pause