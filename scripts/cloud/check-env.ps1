param(
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

$content = Get-Content -LiteralPath $EnvFile -Encoding UTF8
$required = @(
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "DATABASE_URL",
    "YANDEX_CLOUD_FOLDER_ID",
    "YANDEX_OBJECT_STORAGE_BUCKET"
)

$missing = @()
foreach ($name in $required) {
    if (-not ($content -match "^$name=")) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    throw "Missing required env values: $($missing -join ', ')"
}

"Cloud env file contains required keys. Values were not printed."
