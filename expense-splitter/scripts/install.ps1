param (
    [switch]$Dev
)

Write-Host "Starting Expense Splitter Installation..." -ForegroundColor Cyan

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "Found Python: $pythonVersion"

# Create virtual environment
$venvPath = Join-Path $PSScriptRoot "..\.venv"
if (!(Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate and install
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $activateScript
python -m pip install --upgrade pip

$projectRoot = Join-Path $PSScriptRoot ".."
if ($Dev) {
    pip install -e "$projectRoot[dev]"
} else {
    pip install -e "$projectRoot"
}

# Check installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
expense-splitter --help > $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Installation verification failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "Run launcher:"
Write-Host ".\scripts\run-launcher.ps1" -ForegroundColor Cyan
Write-Host "Run CLI:"
Write-Host ".\scripts\run-cli.ps1 --help" -ForegroundColor Cyan
