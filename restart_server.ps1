param(
    [switch]$ClearSession
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "[1/3] Zatrzymywanie procesow python.exe..."
taskkill /f /im python.exe 2>$null | Out-Null
Write-Host "OK: procesy zatrzymane (lub nie byly uruchomione)."

if ($ClearSession) {
    Write-Host "[2/3] Czyszczenie sesji Flask..."
    $sessionPath = Join-Path $PSScriptRoot "instance\flask_session"
    if (Test-Path $sessionPath) {
        Get-ChildItem $sessionPath -File | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "OK: sesje wyczyszczone."
    } else {
        Write-Host "INFO: folder sesji nie istnieje, pomijam."
    }
} else {
    Write-Host "[2/3] Czyszczenie sesji Flask: pominiete (uzyj -ClearSession aby wlaczyc)."
}

Write-Host "[3/3] Uruchamianie serwera Flask..."
& ".venv\Scripts\python.exe" "app.py"
