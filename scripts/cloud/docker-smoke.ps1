param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\smoke-local.ps1" -BaseUrl $BaseUrl
