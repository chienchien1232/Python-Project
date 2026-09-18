$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create .venv and install requirements.txt before starting the dashboard.'
}
& $projectPython -m streamlit run src/app/app.py --server.address 127.0.0.1 --server.port 8520 --server.headless true --browser.gatherUsageStats false
exit $LASTEXITCODE
