param(
    [string]$AppName = "CNBE32-Demo"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $ProjectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "未找到 Python。请先安装 Windows 64 位 Python 3.10+，并勾选 Add python.exe to PATH。"
}

python -m pip install --upgrade pip
python -m pip install -e ".[demo]"

$DbSource = Join-Path $ProjectRoot "src\cnbe32\data\cnbe32.db"
if (-not (Test-Path $DbSource)) {
    throw "未找到运行时数据库：$DbSource"
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name $AppName `
    --collect-data cnbe32 `
    --add-data "src\cnbe32\data\cnbe32.db;cnbe32\data" `
    --hidden-import cnbe32_demo.app `
    --hidden-import cnbe32_demo.presenter `
    "src\cnbe32_demo\app.py"

Write-Host ""
Write-Host "打包完成：dist\$AppName\$AppName.exe"
Write-Host "用于软著演示时，可直接压缩 dist\$AppName 文件夹或复制其中 exe 与依赖文件。"
