[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$failures = [System.Collections.Generic.List[string]]::new()

function Assert-Path {
    param([string]$RelativePath)
    $full = Join-Path $root $RelativePath
    if (-not (Test-Path -LiteralPath $full)) {
        $failures.Add("Missing required path: $RelativePath")
    }
}

$required = @(
    'README.md',
    'docs/ARCHITECTURE.md',
    'docs/PRESERVATION.md',
    'docs/RUNBOOK.md',
    'docs/SECURITY.md',
    'skills/odos-text-studio/SKILL.md',
    'skills/odos-text-studio/scripts/manage_packet.py',
    'skills/odosv5-1/SKILL.md',
    'skills/odosv5-1/scripts/odosv5_state.py',
    'skills/odosv5-1/scripts/build_odosv5_distribution.py',
    'skills/odos-release/SKILL.md',
    'skills/odos-release/scripts/preflight_release.py',
    'skills/odos-media-v1/SKILL.md',
    'skills/odos-media-v1/scripts/odos_media_manager.py'
)
$required | ForEach-Object { Assert-Path $_ }

$skillCount = @(Get-ChildItem -LiteralPath (Join-Path $root 'skills') -Directory).Count
if ($skillCount -ne 4) {
    $failures.Add("Expected 4 skill directories; found $skillCount")
}

$cacheDirs = @(Get-ChildItem -LiteralPath (Join-Path $root 'skills') -Directory -Recurse -Filter '__pycache__')
if ($cacheDirs.Count -gt 0) {
    $failures.Add('Generated __pycache__ directories are present.')
}

$textFiles = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object {
    $_.Extension -in @('.md', '.json', '.yaml', '.yml', '.py', '.ps1', '.html', '.css', '.js')
}
$secretPatterns = @(
    '(?i)(password|passwd)\s*[:=]\s*["''][^"'']+["'']',
    '(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*["''][^"'']+["'']',
    '(?i)cookie\s*[:=]\s*["''][^"'']+["'']',
    '(?i)[A-Z0-9._%+-]+@(gmail|outlook|yahoo|hotmail)\.com',
    '(?i)C:\\Users\\(?!<user>)[^\\]+\\'
)
foreach ($file in $textFiles) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    foreach ($pattern in $secretPatterns) {
        if ($content -match $pattern) {
            $relative = $file.FullName.Substring($root.Length).TrimStart('\')
            $failures.Add("Sensitive-data pattern in $relative")
        }
    }
}

$pythonPath = $env:ODOS_ARCHIVE_PYTHON
if (-not $pythonPath) {
    $pythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonPath = $pythonCommand.Source }
}
if ($pythonPath -and (Test-Path -LiteralPath $pythonPath)) {
    $pythonFiles = Get-ChildItem -LiteralPath (Join-Path $root 'skills') -Recurse -File -Filter '*.py'
    foreach ($file in $pythonFiles) {
        & $pythonPath -m py_compile $file.FullName
        if ($LASTEXITCODE -ne 0) {
            $relative = $file.FullName.Substring($root.Length).TrimStart('\')
            $failures.Add("Python syntax check failed: $relative")
        }
    }
    Get-ChildItem -LiteralPath (Join-Path $root 'skills') -Directory -Recurse -Filter '__pycache__' |
        Remove-Item -Recurse -Force
} else {
    Write-Warning 'Python was not found; structural and sensitive-data checks ran, but Python syntax checks were skipped.'
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

$fileCount = @(Get-ChildItem -LiteralPath (Join-Path $root 'skills') -Recurse -File).Count
Write-Host "ODOS archive verification passed: 4 skills, $fileCount preserved source files."
