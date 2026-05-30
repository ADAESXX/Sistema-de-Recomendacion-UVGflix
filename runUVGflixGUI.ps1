$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (netstat -ano | Select-String "127\.0\.0\.1:7687\s+.*LISTENING")) {
    Write-Host "Neo4j no esta corriendo en 127.0.0.1:7687." -ForegroundColor Yellow
    Write-Host "Abre Neo4j Desktop, inicia tu base de datos y vuelve a correr este script."
    exit 1
}

Set-Location $projectRoot
python -X utf8 gui_uvgflix.py
