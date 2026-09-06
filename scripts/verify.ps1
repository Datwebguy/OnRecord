param (
    [string]$Db
)

$scriptPath = Join-Path $PSScriptRoot "verify.py"
$pyArgs = @()

if ($Db) {
    $pyArgs += "--db"
    $pyArgs += $Db
}

python $scriptPath @pyArgs
