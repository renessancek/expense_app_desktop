[CmdletBinding()]
param(
    [switch]$EnableAutostart
)

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appName = 'Expense App Desktop'
$startMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$shortcutPath = Join-Path $startMenuDir "$appName.lnk"
$iconPath = Join-Path $projectDir 'assets\expense-app-desktop.svg'

if (-not (Test-Path -LiteralPath (Join-Path $projectDir 'start_expense_app.ps1'))) {
    throw 'start_expense_app.ps1 was not found in the project folder.'
}

New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$projectDir\start_expense_app.ps1`""
$shortcut.WorkingDirectory = $projectDir
if (Test-Path -LiteralPath $iconPath) { $shortcut.IconLocation = $iconPath }
$shortcut.Description = 'Manage and categorize expenses'
$shortcut.Save()

if ($EnableAutostart) {
    $startupDir = [Environment]::GetFolderPath('Startup')
    Copy-Item -LiteralPath $shortcutPath -Destination (Join-Path $startupDir "$appName.lnk") -Force
}

Write-Host "Installed '$appName' in the Start menu."
if ($EnableAutostart) { Write-Host 'The app will also start when you sign in.' }
