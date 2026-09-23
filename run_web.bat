@echo off
setlocal

rem Always run relative to the folder containing this launcher.
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [Lan dau] Dang tao moi truong Python va cai thu vien...
    py -3.12 -m venv .venv
    if errorlevel 1 goto :setup_error

    "%PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :setup_error

    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto :setup_error
)

echo.
echo Dang khoi dong World Cup Data Analytics Web App...
echo Trinh duyet se mo tai http://localhost:8520
echo Nhan Ctrl+C trong cua so nay de dung ung dung.
echo.
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:8520'"
"%PYTHON%" -m streamlit run src\app\app.py

echo.
echo Web app da dung.
pause
exit /b

:setup_error
echo.
echo Khong the chuan bi moi truong chay. Hay cai Python 3.12 roi chay lai file nay.
pause
exit /b 1
