param (
    [switch]$Send,
    [string]$Db
)

$scriptPath = Join-Path $PSScriptRoot "proof.py"
$pyArgs = @()

if ($Send) {
    $pyArgs += "--send"
}

if ($Db) {
    $pyArgs += "--db"
    $pyArgs += $Db
}

& python $scriptPath @pyArgs
