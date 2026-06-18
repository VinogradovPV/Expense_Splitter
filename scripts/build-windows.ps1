param (
    [switch]$NoUpx
)

Write-Host "Starting Expense Splitter Windows Build..." -ForegroundColor Cyan

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Create virtual environment if not exists
$venvPath = Join-Path $PSScriptRoot "..\.venv"
if (!(Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate and install build dependencies
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "Installing build dependencies..." -ForegroundColor Yellow
& $activateScript
python -m pip install --upgrade pip
pip install pyinstaller

# Run PyInstaller
$projectRoot = Join-Path $PSScriptRoot ".."
$packagingDir = Join-Path $projectRoot "packaging"
$specFile = Join-Path $packagingDir "expense_splitter.spec"

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Set-Location $packagingDir

$pyinstallerCommand = "pyinstaller --clean --workpath build --distpath dist --specpath ."
if ($NoUpx) {
    $pyinstallerCommand += " --noupx"
}
$pyinstallerCommand += " $specFile"

Invoke-Expression $pyinstallerCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: PyInstaller build failed." -ForegroundColor Red
    exit 1
}

Set-Location $projectRoot

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Executables are in the 'dist' folder:" -ForegroundColor Green
Get-ChildItem -Path "$projectRoot\dist" -Filter "*.exe"
