param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$TenantId = "local"
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Invoke-JsonPost {
    param(
        [string]$Uri,
        [hashtable]$Body
    )
    Invoke-RestMethod `
        -Method Post `
        -Uri $Uri `
        -Headers @{ "X-Tenant-Id" = $TenantId } `
        -ContentType "application/json" `
        -Body ($Body | ConvertTo-Json -Depth 8)
}

$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
if (-not $health.ok) {
    throw "Backend healthcheck failed."
}

$reporting = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health/reporting"
if (-not $reporting.ok -or -not $reporting.reportlab -or -not $reporting.openpyxl) {
    throw "Reporting healthcheck failed."
}

$pdfReport = Invoke-JsonPost `
    -Uri "$BaseUrl/api/current-report" `
    -Body @{ scope = "open"; formats = @("pdf") }

$xlsxReport = Invoke-JsonPost `
    -Uri "$BaseUrl/api/current-report" `
    -Body @{ scope = "open"; formats = @("xlsx") }

[PSCustomObject]@{
    backend = $health
    reporting = $reporting
    pdf_report_id = $pdfReport.report_id
    xlsx_report_id = $xlsxReport.report_id
}
