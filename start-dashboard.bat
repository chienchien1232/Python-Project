@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "APP=%~dp0src\app\app.py"
set "REQUIREMENTS=%~dp0requirements.txt"

if not exist "%REQUIREMENTS%" (
    echo Khong tim thay requirements.txt.
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo Chua co .venv. Dang tao moi truong ao...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.12 -m venv .venv
        if errorlevel 1 python -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo Khong tao duoc .venv. Hay cai Python 3.12 va thu lai.
        pause
        exit /b 1
    )
)

if not exist "%APP%" (
    echo Khong tim thay Streamlit app: "%APP%"
    pause
    exit /b 1
)

echo Dang kiem tra va cai dat requirements.txt vao .venv...
"%PYTHON%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo Cai dat requirements that bai. Kiem tra ket noi mang va thu lai.
    pause
    exit /b 1
)

echo Dang khoi dong World Cup Dashboard...
echo Trinh duyet se mo tai http://127.0.0.1:8520/
"%PYTHON%" -m streamlit run src/app/app.py --server.address 127.0.0.1 --server.port 8520 --server.headless false --browser.gatherUsageStats false

if errorlevel 1 (
    echo.
    echo Dashboard dung do co loi. Kiem tra thong bao phia tren.
    pause
)
