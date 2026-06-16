param (
    [switch]$RemoveData
)

Write-Host "Starting Expense Splitter Uninstallation..." -ForegroundColor Cyan

$venvPath = Join-Path $PSScriptRoot "..\.venv"

if (Test-Path $venvPath) {
    Write-Host "Removing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
    Write-Host "Virtual environment removed." -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found."
}

if ($RemoveData) {
    $dataPath = Join-Path $PSScriptRoot "..\data"
    $reportsPath = Join-Path $PSScriptRoot "..\reports"
    
    if (Test-Path $dataPath) {
        Write-Host "Removing data directory..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $dataPath
    }
    if (Test-Path $reportsPath) {
        Write-Host "Removing reports directory..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $reportsPath
    }
    Write-Host "User data and reports removed." -ForegroundColor Green
} else {
    Write-Host "User data preserved. Use -RemoveData flag to delete it." -ForegroundColor Yellow
}

Write-Host "Uninstallation completed." -ForegroundColor Green
