$ErrorActionPreference = 'Stop'
$psql = (Get-Command psql -ErrorAction SilentlyContinue).Source
if (-not $psql) { $candidate = 'C:\Program Files\PostgreSQL\17\bin\psql.exe'; if (Test-Path $candidate) { $psql = $candidate } }
if (-not $psql) { throw 'psql.exe not found. Run setup-native.ps1 from an elevated PowerShell first.' }
Start-Service -Name 'postgresql-x64-17' -ErrorAction SilentlyContinue
$env:PGPASSWORD = 'integration_dev'
& $psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -c "DO `$`$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'integration') THEN CREATE ROLE integration LOGIN PASSWORD 'integration_dev'; END IF; END `$`$;"
& $psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -c "SELECT 'CREATE DATABASE integration OWNER integration' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'integration')\gexec"
Remove-Item Env:PGPASSWORD
Push-Location (Join-Path $PSScriptRoot '..\backend')
alembic upgrade head
Pop-Location
Write-Host 'PostgreSQL configured: localhost:5432/integration (integration/integration_dev).'
