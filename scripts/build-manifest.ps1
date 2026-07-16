[CmdletBinding()]
param(
    [string]$SnapshotDate = '2026-07-16'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$skillsRoot = Join-Path $root 'skills'

$skills = foreach ($directory in Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object Name) {
    $files = foreach ($file in Get-ChildItem -LiteralPath $directory.FullName -Recurse -File | Sort-Object FullName) {
        [ordered]@{
            path = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
            bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    [ordered]@{
        name = $directory.Name
        file_count = @($files).Count
        files = @($files)
    }
}

$manifest = [ordered]@{
    schema_version = 1
    snapshot_date = $SnapshotDate
    source = 'Local Codex skill installations, sanitized public snapshot'
    normalizations = @(
        'Machine-specific Text Studio home path changed to a portable user-home path.',
        'Inactive fallback email changed to alerts@example.invalid.',
        'Generated Python bytecode caches excluded.'
    )
    skills = @($skills)
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'archive-manifest.json') -Encoding UTF8
Write-Host "Wrote archive-manifest.json for $(@($skills).Count) skills."

