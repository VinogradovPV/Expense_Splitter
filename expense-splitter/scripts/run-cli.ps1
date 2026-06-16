$venvPath = Join-Path $PSScriptRoot "..\.venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (!(Test-Path $activateScript)) {
    Write-Host "Virtual environment not found. Please run install.ps1 first." -ForegroundColor Red
    exit 1
}

& $activateScript
expense-splitter $args
