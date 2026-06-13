Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

python -m compileall backend ml_service
python -m pytest backend\tests ml_service\tests
Push-Location frontend
try {
  & "C:\Program Files\nodejs\npm.cmd" run build
}
finally {
  Pop-Location
}
