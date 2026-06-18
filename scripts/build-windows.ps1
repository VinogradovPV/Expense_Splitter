param (
    [switch]$NoUpx
)

$ErrorActionPreference = "Stop"

Write-Host "Starting Expense Splitter Windows Build..." -ForegroundColor Cyan

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Create virtual environment if not exists
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPath = Join-Path $projectRoot ".venv"
if (!(Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate and install build dependencies
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "Installing build dependencies..." -ForegroundColor Yellow
& $activateScript
python -m pip install --upgrade pip
python -m pip install -e "${projectRoot}[dev]"

# Run PyInstaller
$packagingDir = Join-Path $projectRoot "packaging"
$specFile = Join-Path $packagingDir "expense_splitter.spec"
$buildDir = Join-Path $projectRoot "build"
$distDir = Join-Path $projectRoot "dist"

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Push-Location $projectRoot
$pyinstallerArgs = @(
    "--clean",
    "--workpath", $buildDir,
    "--distpath", $distDir
)
if ($NoUpx) {
    $env:PYINSTALLER_NO_UPX = "1"
} else {
    Remove-Item Env:\PYINSTALLER_NO_UPX -ErrorAction SilentlyContinue
}
$pyinstallerArgs += $specFile

try {
    python -m PyInstaller @pyinstallerArgs
}
finally {
    Remove-Item Env:\PYINSTALLER_NO_UPX -ErrorAction SilentlyContinue
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: PyInstaller build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Executables are in the 'dist' folder:" -ForegroundColor Green
Get-ChildItem -Path $distDir -Filter "*.exe"
