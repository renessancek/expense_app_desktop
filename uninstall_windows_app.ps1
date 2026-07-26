[CmdletBinding()]
param(
    [switch]$KeepAutostart
)

$ErrorActionPreference = 'Stop'
$appName = 'Expense App Desktop'
$shortcutPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$appName.lnk"
$startupPath = Join-Path ([Environment]::GetFolderPath('Startup')) "$appName.lnk"

if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
    Write-Host 'Removed Start menu shortcut.'
}
if (-not $KeepAutostart -and (Test-Path -LiteralPath $startupPath)) {
    Remove-Item -LiteralPath $startupPath -Force
    Write-Host 'Removed autostart shortcut.'
}
