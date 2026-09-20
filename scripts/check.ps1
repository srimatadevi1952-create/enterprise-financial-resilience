param([ValidateSet('development','test')][string]$Profile='test')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    & '.\.venv\Scripts\python.exe' -m resilience.cli doctor --profile $Profile
    if ($LASTEXITCODE -ne 0) { throw 'Environment check failed' }
} finally { Pop-Location }
