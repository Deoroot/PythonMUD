Param(
    [string]$Python312Exe = "py -3.12",
    [string]$VenvPath = ".venv312"
)

Write-Host "Setting up Evennia-compatible environment (Python 3.12)..."

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher 'py' not found. Install Python 3.12 first."
    exit 1
}

# Create venv with Python 3.12
& py -3.12 -m venv $VenvPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not create venv with Python 3.12. Verify installation via: py -0p"
    exit 1
}

$python = Join-Path $VenvPath "Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install setuptools pywin32

Write-Host "Environment ready."
Write-Host "Activate with: .\\$VenvPath\\Scripts\\Activate.ps1"
Write-Host "Then run Evennia commands from helionvanta with:"
Write-Host "  python ../tools/evennia_cli.py migrate"
Write-Host "  python ../tools/evennia_cli.py start"
