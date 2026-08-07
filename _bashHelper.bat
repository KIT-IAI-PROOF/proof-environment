@echo off
REM _bashHelper.bat
REM Detects Git Bash and a suitable non-Docker WSL distro.
REM Must be called with: call "%SCRIPT_DIR%_bashHelper.bat"
REM Do NOT add setlocal here — variables must survive back into the caller.
REM
REM Output variables set in the caller's environment:
REM   PROOF_BASH_TYPE    — gitbash | wsl | none
REM   PROOF_GIT_BASH     — full path to bash.exe (gitbash only)
REM   PROOF_WSL_DISTRO   — chosen distro name, or "default" to use the WSL system default
REM   PROOF_WSL_DEFAULT  — name of the WSL system default distro

set "PROOF_BASH_TYPE="
set "PROOF_GIT_BASH="
set "PROOF_WSL_DISTRO="
set "PROOF_WSL_DEFAULT="

REM --- 1. Detect Git Bash ---
REM   Locate git.exe, then derive bash.exe from the sibling bin\ folder.
for /f "delims=" %%i in ('where git 2^>nul') do (
    if not defined PROOF_GIT_BASH (
        for %%j in ("%%~dpi..\bin\bash.exe") do set "PROOF_GIT_BASH=%%~fj"
    )
)

if defined PROOF_GIT_BASH (
    if exist "%PROOF_GIT_BASH%" (
	    echo Running with Git Bash: %PROOF_GIT_BASH%
        set "PROOF_BASH_TYPE=gitbash"
        goto :eof
    )
)

REM --- 2. Git Bash not found — detect a suitable WSL distro ---
REM   Priority list: first match that is actually installed wins.
echo Git Bash not found, falling back to WSL...

set "PROOF_WSL_DISTRO_LIST=Ubuntu Ubuntu-24.04 Ubuntu-22.04 Ubuntu-20.04"

for /f "delims=" %%d in ('wsl -e sh -c "echo $WSL_DISTRO_NAME" 2^>nul') do set "PROOF_WSL_DEFAULT=%%d"

REM If the system default distro is a Docker-internal distro it cannot be used directly.
REM findstr exits 0 when "docker" is found (errorlevel 0 = match = it IS a Docker distro).
echo %PROOF_WSL_DEFAULT%| findstr /i "docker" >nul
if not errorlevel 1 (
    REM Default is a Docker distro — search PROOF_WSL_DISTRO_LIST for an installed Ubuntu
    for %%n in (%PROOF_WSL_DISTRO_LIST%) do (
        if not defined PROOF_WSL_DISTRO (
            REM wsl --list outputs UTF-16; PowerShell strips non-printable bytes before matching.
            powershell -NoProfile -Command "$l = wsl --list --quiet 2>$null | ForEach-Object { $_ -replace '[^a-zA-Z0-9\-\.]','' }; if ($l -icontains '%%n') { exit 0 } else { exit 1 }" 2>nul
            if not errorlevel 1 set "PROOF_WSL_DISTRO=%%n"
        )
    )
) else (
    REM Default distro is not Docker — safe to use it directly
	echo Using default WSL distro
    set "PROOF_WSL_DISTRO=%PROOF_WSL_DEFAULT%"
)

if defined PROOF_WSL_DISTRO (
	echo Running with WSL distro: %PROOF_WSL_DISTRO%
    set "PROOF_BASH_TYPE=wsl"
) else (
    echo No suitable WSL distro found.
    echo Checked: %PROOF_WSL_DISTRO_LIST%
    echo Default distro was: %PROOF_WSL_DEFAULT%
    echo Please install git bash (https://git-scm.com/install/windows) or one of the above Ubuntu distros in WSL, or extend PROOF_WSL_DISTRO_LIST in _bashHelper.bat.
    set "PROOF_BASH_TYPE=none"
)
