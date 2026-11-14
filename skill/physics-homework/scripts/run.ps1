# Windows entry point. Does not change execution policy, system Python or shell profiles.
$ErrorActionPreference = 'Stop'
$Work = if ($env:PHYSICS_HOME) { $env:PHYSICS_HOME } else { Join-Path $HOME 'codex/physics-homework' }
New-Item -ItemType Directory -Force -Path "$Work/.tools", "$Work/.cache", "$Work/tmp" | Out-Null
$env:UV_CACHE_DIR = "$Work/.cache/uv"
$env:UV_PYTHON_INSTALL_DIR = "$Work/.python"
$env:UV_PYTHON_BIN_DIR = "$Work/.tools"
$env:TEMP = "$Work/tmp"
$env:TMP = "$Work/tmp"
$Python = "$Work/.venv/Scripts/python.exe"
$Ready = $false
if (Test-Path $Python) {
    & $Python -c 'import PIL,pypdf,pdfplumber,reportlab,pypdfium2' 2>$null
    $Ready = ($LASTEXITCODE -eq 0)
}
if (-not $Ready) {
    [Console]::Error.WriteLine('首次使用：正在自动准备独立运行环境。')
    $UV = "$Work/.tools/uv.exe"
    if (-not (Test-Path $UV)) {
        $Installed = Get-Command uv -ErrorAction SilentlyContinue
        if ($Installed) { $UV = $Installed.Source } else {
            $env:UV_INSTALL_DIR = "$Work/.tools"
            $env:UV_NO_MODIFY_PATH = '1'
            Invoke-WebRequest 'https://astral.sh/uv/install.ps1' -OutFile "$Work/tmp/install-uv.ps1"
            & "$Work/tmp/install-uv.ps1"
            if ($LASTEXITCODE -ne 0) { throw '运行环境安装未完成。' }
        }
    }
    if (-not (Test-Path $Python)) {
        & $UV venv --python 3.12 "$Work/.venv"
        if ($LASTEXITCODE -ne 0) { throw 'Python环境准备未完成。' }
    }
    & $UV pip install --python $Python -r "$PSScriptRoot/requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw '依赖准备未完成。' }
}
if ($args.Count -gt 0 -and $args[0] -eq 'qa') {
    & $Python "$PSScriptRoot/qa_pdf.py" @($args | Select-Object -Skip 1)
} else {
    & $Python "$PSScriptRoot/homework.py" --workspace $Work @args
}
exit $LASTEXITCODE
