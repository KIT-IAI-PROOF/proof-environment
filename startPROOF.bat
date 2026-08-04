@echo off
REM Windows batch file to start PROOF services using git bash or WSL
REM This leverages the bash startPROOF script via bash or Windows Subsystem for Linux

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "WIN_DIR=%SCRIPT_DIR:~0,-1%"
set "UNIX_DIR=%WIN_DIR:\=/%"

REM Detect Git Bash / WSL distro
call "%SCRIPT_DIR%_bashHelper.bat"

if "%PROOF_BASH_TYPE%"=="gitbash" (
	"%PROOF_GIT_BASH%" --login -i -c "'%UNIX_DIR%/startPROOF' -d %*"
) else if "%PROOF_BASH_TYPE%"=="wsl" (
	wsl -d %PROOF_WSL_DISTRO% cd "`wslpath '%WIN_DIR%'`" ^&^& ./startPROOF %*
) else (
	echo ERROR: Neither Git Bash nor WSL found. Please install Git for Windows or WSL.
	call :nativeCall
	goto :end
)

REM If the bash command returned an error, try the native call as a fallback.
if errorlevel 1 (
	call :nativeCall
)

:end
pause
exit /b

REM Try native call as last resort if an error occurred.
REM This is not preferred as it does not include some user friendly features.
:nativeCall
	echo An error occurred. Trying with direct call:
	echo docker compose -f docker/docker-compose.prod.yaml --env-file docker/proof.env up
	docker compose -f docker/docker-compose.prod.yaml --env-file docker/proof.env up
goto :eof