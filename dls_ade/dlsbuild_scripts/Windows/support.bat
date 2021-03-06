:: ****************************************************************************
:: 
:: Script to build a Diamond production module in the support or ioc areas
::
:: This is a partial script which builds a module for the dls-release
:: system. The script is prepended with a list of variables before invocation
:: by the dls-release mechanism. These variables are:
::
::   _profile   : Optional override of the profile batch script
::   _email     : The email address of the user who initiated the build
::   _epics     : The DLS_EPICS_RELEASE to use
::   _build_dir : The parent directory in the file system in which to build the
::                module. This does not include module or version directories.
::   _git_dir   : The Git URL to clone
::   _module    : The module name
::   _version   : The module version
::   _area      : The build area
::   _force     : Force the build (i.e. rebuild even if already exists)
::   _build_name: The base name to use for log files etc.
::

setlocal enabledelayedexpansion enableextensions

:: Set up environment
set DLS_EPICS_RELEASE=%_epics%
if defined _profile (
    call %_profile%
) else (
    call W:\etc\profile.bat
)
echo on
if errorlevel 1 (
    call :ReportFailure %ERRORLEVEL% Could not find profile. Aborting build.
)

set "build_dir=%_build_dir:/=\%\%_module%"

:: Checkout module
mkdir "%build_dir%"
if errorlevel 1 (
    call :ReportFailure %ERRORLEVEL% Can not mkdir %build_dir%
)

cd /d "%build_dir%"
if errorlevel 1 (
    call :ReportFailure %ERRORLEVEL% Can not cd to %build_dir%
)

(echo %build_dir% | findstr /i /c:"prod" >nul) && (set is_test="false") || (set is_test="true")

if not exist %_version% (
    if %is_test% == "false" (
        git clone --depth=100 %_git_dir% %_version%
    ) else (
        git clone %_git_dir% %_version%
    )
    if errorlevel 1 (
        call :ReportFailure %ERRORLEVEL% Can not clone %_git_dir%
    )
    if %is_test% == "false" (
        pushd %_version% && git fetch --tags && git checkout %_version% && popd
    ) else (
        pushd %_version% && git checkout %_version% && popd
    )
    if errorlevel 1 (
        call :ReportFailure %ERRORLEVEL% Can not checkout %_version%
    )

) else if "%_force%"=="true" (
    rmdir /s/q %_version%
    if errorlevel 1 (
        call :ReportFailure %ERRORLEVEL% Can not remove %_version%
    )
    if %is_test% == "false" (
        git clone --depth=100 %_git_dir% %_version%
    ) else (
        git clone %_git_dir% %_version%
    )
    if errorlevel 1 (
        call :ReportFailure %ERRORLEVEL% Can not clone %_git_dir%
    )
    if %is_test% == "false" (
        pushd %_version%  && git fetch --tags && git checkout %_version% && popd
    ) else (
        pushd %_version%  && git checkout %_version% && popd
    )
    if errorlevel 1 (
        call :ReportFailure %ERRORLEVEL% Can not checkout %_version%
    )

) else (
    pushd %_version%
    For /f "delims=" %%a in ('git status -uno --porcelain^| findstr /V /R /c:"^ M configure/RELEASE\..*" ^| findstr /V /R /c:"^ M configure/RELEASE" ^| find /v /c ""') do (set _nlines=%%a)
    popd
    if not "%_nlines%" == "0" (
        call :ReportFailure 1 Directory %build_dir%/%_version% not up to date with %_git_dir%
    )

)

cd "%_version%"
if errorlevel 1 (
    call :ReportFailure %ERRORLEVEL% Can not cd to %_version%
)

:: Modify configure\RELEASE
git cat-file -p HEAD:configure/RELEASE > configure\RELEASE.vcs

del configure\RELEASE
for /f "delims=" %%i in ( configure\RELEASE.vcs ) do (
    set TMP_LINE=%%i
    set TMP_LINE=!TMP_LINE: =!

    if "!TMP_LINE:~0,5!"=="WORK=" (
        echo # WORK=commented out to prevent prod modules depending on work modules>> configure\RELEASE
    ) else (
        echo %%i>> configure\RELEASE
    )
)

echo EPICS_BASE=%EPICS_BASE:\=/%>  configure\RELEASE.%EPICS_HOST_ARCH%
echo SUPPORT=W:/prod/%_epics:_64=%/support>> configure\RELEASE.%EPICS_HOST_ARCH%

copy configure\RELEASE.%EPICS_HOST_ARCH% configure\RELEASE.%EPICS_HOST_ARCH%.Common

git ls-files configure/VERSION --error-unmatch >NUL 2>&1
if not errorlevel 1 (
    call :ReportFailure 1 configure\VERSION must not be in version control
)
echo %_version% > configure\VERSION

:: Build
set error_log=%_build_name%.err
set build_log=%_build_name%.log

%_make% clean
:: make
%_make% 1>%build_log% 2>%error_log%
set make_status=%ERRORLEVEL%
echo %make_status% > %_build_name%.sta
if NOT "%make_status%"=="0" call :ReportFailure %make_status% Build Errors for %_module% %_version%

goto :EOF

:ReportFailure
    if exist "%build_dir%/%_version%" echo %1 > "%build_dir%\%_version%\%_build_name%.sta"
    echo #### ERROR [%DATE% %TIME%] ### Error code: %*
    exit /B %1
    goto :EOF
