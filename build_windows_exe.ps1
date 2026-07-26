[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = Join-Path $projectDir 'venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $python)) { throw 'Virtual environment not found. Install dependencies first.' }
Set-Location -LiteralPath $projectDir
& $python -m PyInstaller --noconfirm --clean --windowed --name 'Expense App Desktop' --add-data 'assets;assets' desktop_app.py
