@echo off
REM Windows batch file to control PROOF services using git bash or WSL
REM Dynamically reads available options from the controlPROOF bash script

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "WIN_DIR=%SCRIPT_DIR:~0,-1%"
set "UNIX_DIR=%WIN_DIR:\=/%"

REM Detect Git Bash / WSL distro
call "%SCRIPT_DIR%_bashHelper.bat"

if "%PROOF_BASH_TYPE%"=="none" (
    echo ERROR: Neither Git Bash nor WSL found. Please install Git for Windows or WSL.
    pause
    exit /b 1
)

REM Show help
call :callControlPROOF -h

REM Prompt user for option selection
echo.
set "CHOSEN_FLAG=--stop"
set /p "CHOSEN_FLAG=Which option you want to select [default: --stop]: "
if "%CHOSEN_FLAG%"=="" set "CHOSEN_FLAG=--stop"

REM Prepend dash if missing
set "flagStart=%CHOSEN_FLAG:~0,1%"
if not "%flagStart%"=="-" set "CHOSEN_FLAG=-%CHOSEN_FLAG%"

echo.
echo Running: controlPROOF %CHOSEN_FLAG%
echo.

call :callControlPROOF %CHOSEN_FLAG%

pause
exit /b

REM Execute controlPROOF with the chosen flag as param e.g call :callControlPROOF -h
:callControlPROOF
    if "%PROOF_BASH_TYPE%"=="gitbash" (
        "%PROOF_GIT_BASH%" --login "%WIN_DIR%\controlPROOF" %*
    ) else if "%PROOF_BASH_TYPE%"=="wsl" (
        wsl -d %PROOF_WSL_DISTRO% bash "$(wslpath '%WIN_DIR%')/controlPROOF" %*
    ) else (
        echo ERROR: No bash environment available to run controlPROOF.
    )
goto :eof