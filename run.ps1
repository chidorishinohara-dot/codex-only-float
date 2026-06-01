$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$existing = Get-CimInstance Win32_Process |
  Where-Object {
    ($_.Name -in @("python.exe", "pythonw.exe")) -and
    ($_.CommandLine -like "*codex_quota_float.py*")
  }
if ($existing) {
  exit 0
}

$pythonw = Get-Command pythonw -All -ErrorAction SilentlyContinue |
  Where-Object { $_.Source -notlike "*\WindowsApps\pythonw.exe" } |
  Select-Object -First 1 -ExpandProperty Source
if ($pythonw) {
  Start-Process -FilePath $pythonw -ArgumentList "`"$PSScriptRoot\codex_quota_float.py`"" -WorkingDirectory $PSScriptRoot
} else {
  python .\codex_quota_float.py
}
