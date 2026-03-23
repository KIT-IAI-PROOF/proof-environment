@echo off
REM Windows batch file to start PROOF services using WSL
REM This leverages the bash startPROOF script via Windows Subsystem for Linux

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Convert Windows path to WSL path and run the bash script
wsl -d Ubuntu cd "`wslpath '%SCRIPT_DIR%'`" ^&^& ./startPROOF %*

pause