# Build UniversalFileOrganizer.exe for Windows 10/11, 64-bit.
#
# This script does not change the Windows PATH or Registry. It only creates
# PyInstaller's generated build files and the final file in the dist folder.
# Run it from the project folder in a normal PowerShell window.

$ErrorActionPreference = "Stop"

function Stop-Build($message) {
    Write-Error $message
    exit 1
}

# Prefer the project's Python 3.13 installation when the Python launcher can
# find it. Fall back to the regular python command if needed.
$pythonCommand = $null
$pythonArguments = @()
$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$regularPython = Get-Command python -ErrorAction SilentlyContinue

if ($pythonLauncher) {
    & py -3.13 -c "import sys; assert sys.version_info >= (3, 10); print(sys.version)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = "py"
        $pythonArguments = @("-3.13")
    }
}

if (-not $pythonCommand -and $regularPython) {
    & python -c "import sys; assert sys.version_info >= (3, 10); print(sys.version)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = "python"
    }
}

if (-not $pythonCommand) {
    Stop-Build "Python 3.13 was not found. Install Python 3.13 for Windows, then run this script again."
}

Write-Host "Using Python command: $pythonCommand $($pythonArguments -join ' ')"

# Check rather than install PyInstaller automatically. This keeps the build
# predictable and makes the required network-dependent step explicit.
& $pythonCommand @pythonArguments -m PyInstaller --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller is not installed for this Python interpreter."
    Write-Host "Install it with this command, then run build_exe.ps1 again:"
    Write-Host "  $pythonCommand $($pythonArguments -join ' ') -m pip install pyinstaller"
    exit 1
}

$projectFolder = (Get-Location).Path
$entryPoint = Join-Path $projectFolder "app_entry.py"
$distFolder = Join-Path $projectFolder "dist"
$buildFolder = Join-Path $projectFolder "build\pyinstaller"

if (-not (Test-Path -LiteralPath $entryPoint -PathType Leaf)) {
    Stop-Build "The entry point was not found: $entryPoint"
}

Write-Host "Building one console executable..."
& $pythonCommand @pythonArguments -m PyInstaller `
    --onefile `
    --console `
    --clean `
    --name UniversalFileOrganizer `
    --distpath $distFolder `
    --workpath $buildFolder `
    --specpath $buildFolder `
    --hidden-import tkinter `
    $entryPoint

if ($LASTEXITCODE -ne 0) {
    Stop-Build "PyInstaller failed. Read the error messages above. No personal files were removed."
}

$executable = Join-Path $distFolder "UniversalFileOrganizer.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    Stop-Build "PyInstaller reported success, but the expected executable was not found: $executable"
}

Write-Host ""
Write-Host "Build succeeded. The standalone executable is:"
Write-Host $executable
Write-Host ""
Write-Host "The generated PyInstaller work files are in: $buildFolder"
