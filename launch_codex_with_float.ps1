$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Launch Codex first, then open the quota float after the Codex process appears.
Start-Process explorer.exe "shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App"

$deadline = (Get-Date).AddSeconds(20)
do {
  Start-Sleep -Milliseconds 500
  $codexRunning = @(
    Get-CimInstance Win32_Process |
      Where-Object { $_.Name -eq "Codex.exe" -and $_.CommandLine -like "*OpenAI.Codex*" }
  ).Count -gt 0
} until ($codexRunning -or (Get-Date) -gt $deadline)

powershell -ExecutionPolicy Bypass -File .\run.ps1
