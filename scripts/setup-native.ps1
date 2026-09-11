$ErrorActionPreference = 'Stop'
Write-Host 'Installing native PostgreSQL 16 and RabbitMQ (run PowerShell as Administrator).'
if (Get-Command choco -ErrorAction SilentlyContinue) { choco install postgresql16 rabbitmq -y --no-progress } else { winget install --id PostgreSQL.PostgreSQL.16 --exact --accept-source-agreements --accept-package-agreements; winget install --id RabbitMQ.RabbitMQ --exact --accept-source-agreements --accept-package-agreements }
Write-Host 'Start services with: Start-Service postgresql-x64-16; Start-Service RabbitMQ'
