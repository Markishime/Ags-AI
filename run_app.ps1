param(
    [int]$Port = 8501
)

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error ".venv not found. Create it and install requirements first."
    exit 1
}

& $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py") --server.headless true --server.port $Port

