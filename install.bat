@echo off
chcp 65001 >nul
title AI Agent Repair Tool - 一键安装
echo ============================================================
echo  AI Agent 智能修复工具 - 一键安装
echo ============================================================
echo.

:: 检查 git
where git >nul 2>&1
if errorlevel 1 (
    echo [!] 未检测到 Git，正在下载...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.45.0.windows.1/Git-2.45.0-64-bit.exe' -OutFile '%TEMP%\git-installer.exe'"
    start /wait "" "%TEMP%\git-installer.exe" /VERYSILENT
    del "%TEMP%\git-installer.exe" 2>nul
)

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [!] 未检测到 Python，正在下载...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1
    del "%TEMP%\python-installer.exe" 2>nul
    :: 刷新环境变量
    set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
)

:: 获取用户桌面路径
for /f "usebackq" %%d in (`powershell -Command "[Environment]::GetFolderPath('Desktop')"`) do set DESKTOP=%%d

:: 克隆项目
echo [1/3] 正在下载项目...
if not exist "%DESKTOP%\ai-agent-repair-tool" (
    cd /d "%DESKTOP%"
    git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
    if errorlevel 1 (
        echo [!] 下载失败，请检查网络连接
        pause
        exit /b 1
    )
) else (
    echo [OK] 项目已存在，跳过下载
)

:: 进入项目目录
cd /d "%DESKTOP%\ai-agent-repair-tool"

:: 安装依赖
echo [2/3] 正在安装依赖...
python -m pip install -r requirements.txt --quiet 2>nul

:: 创建桌面快捷方式
echo [3/3] 创建启动快捷方式...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\AI修复工具.lnk'); $s.TargetPath = 'python'; $s.Arguments = 'gui.py'; $s.WorkingDirectory = '%DESKTOP%\ai-agent-repair-tool'; $s.IconLocation = 'python.exe,0'; $s.Save()"

echo.
echo ============================================================
echo  安装完成！
echo ============================================================
echo.
echo  启动方式：
echo    1. 双击桌面 [AI修复工具] 快捷方式
echo    2. 或双击项目中的 run.bat
echo.
echo  项目位置：%DESKTOP%\ai-agent-repair-tool
echo ============================================================
echo.
pause
