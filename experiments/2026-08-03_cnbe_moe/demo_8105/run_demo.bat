@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请安装 Windows 64 位 Python 3.10+ 并勾选 Add python.exe to PATH。
    pause
    exit /b 1
)

python -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 当前 Python 缺少 tkinter，请安装标准 Windows 版 Python。
    pause
    exit /b 1
)

start "" pythonw app.py
if errorlevel 1 (
    python app.py
)
endlocal
