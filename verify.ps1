<#
.SYNOPSIS
    OnRecord Sibyl Memory & Delete Test Verification
.DESCRIPTION
    Runs the automated proof verifying that Clerk is completely blind without
    storage files, that wiping tenant_scout drops the queue to 0, and restores
    the database automatically.
#>

param (
    [string]$Db
)

$scriptPath = Join-Path $PSScriptRoot "scripts" "verify.py"
if (-not (Test-Path $scriptPath)) {
    $scriptPath = Join-Path $PSScriptRoot "verify.py"
}

$pyArgs = @()
if ($Db) {
    $pyArgs += "--db"
    $pyArgs += $Db
}

python $scriptPath @pyArgs
