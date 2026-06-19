param(
    [Alias("h")]
    [switch]$Help,
    [string]$DataDir = "data",
    [string]$ReportsDir = "reports"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$GuiExe = Join-Path $ProjectRoot ".venv\Scripts\expense-splitter-gui.exe"

if ($Help) {
    Write-Host "Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 [-DataDir data] [-ReportsDir reports]"
    Write-Host ""
    Write-Host "Starts the Expense Splitter desktop GUI launcher."
    return
}

if (!(Test-Path $GuiExe)) {
    Write-Host "GUI entry point not found. Run installer first:" -ForegroundColor Yellow
    Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1"
    exit 1
}

& $GuiExe --data-dir $DataDir --reports-dir $ReportsDir
