param(
    [string]$Image = "expense-splitter-backend:local"
)

$ErrorActionPreference = "Stop"
docker build --pull -t $Image .
