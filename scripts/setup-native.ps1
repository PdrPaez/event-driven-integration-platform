$ErrorActionPreference = 'Stop'
Write-Host 'Installing native PostgreSQL 17 and RabbitMQ (run PowerShell as Administrator).'
if (Get-Command choco -ErrorAction SilentlyContinue) { choco install postgresql17 rabbitmq -y --no-progress } else { winget install --id PostgreSQL.PostgreSQL.17 --exact --accept-source-agreements --accept-package-agreements --silent; choco install rabbitmq -y --no-progress }
Write-Host 'Run .\scripts\configure-postgres.ps1 after installation.'
