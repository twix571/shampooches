@echo off
setlocal enabledelayedexpansion

set "TEMP_FILE=%TEMP%\project_code_%RANDOM%%RANDOM%.txt"
set "PROJECT_DIR=%~dp0"
set "MAX_FILE_SIZE=10485760"
set "TOTAL_FILES=0"
set "SKIPPED_FILES=0"
set "TOTAL_SIZE=0"

echo Copying all files from project to clipboard...
echo Max file size: %MAX_FILE_SIZE% bytes
echo.

rem Create temp file with error checking
echo. > "%TEMP_FILE%" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot create temp file: %TEMP_FILE%
    echo Please check TEMP directory permissions
    pause
    exit /b 1
)

rem Iterate through all files in project using dir for better handling
for /f "delims=" %%f in ('dir /s /b /a-d "%PROJECT_DIR%*" 2^>nul') do (
    set "skip_file=0"
    set "ext=%%~xf"
    set "filepath=%%f"
    
    rem Get file size
    for %%A in ("%%f") do set "file_size=%%~zA"
    
    rem Skip files larger than MAX_FILE_SIZE (10MB)
    if !file_size! GTR %MAX_FILE_SIZE% (
        set "skip_file=1"
        set "skip_reason=too large"
    )
    
    rem Skip binary files by extension using findstr
    echo !ext! | findstr /r /i "\.sqlite3 \.db \.pyc \.pyd \.pdf \.exe \.dll \.so \.dylib \.bin \.data \.png \.jpg \.jpeg \.gif \.ico \.bmp \.woff \.woff2 \.ttf \.eot \.svg \.mp3 \.mp4 \.avi \.mov \.zip \.tar \.gz \.rar \.7z" >nul 2>&1
    if !errorlevel! == 0 (
        set "skip_file=1"
        set "skip_reason=binary extension"
    )
    
    rem Skip the batch file itself
    if /i "%%~nxf"=="copy_to_clipboard(neverDelete).bat" (
        set "skip_file=1"
        set "skip_reason=batch file itself"
    )
    
    rem Skip if file is in exclude directories (combining into one command for efficiency)
    echo !filepath! | findstr /i /c:"\\node_modules\\" /c:"\\venv\\" /c:"\.venv\\" /c:"\\env\\" /c:"\\virtualenv\\" /c:"\.git\\" /c:"\\__pycache__\\" /c:"\.tox\\" /c:"\\dist\\" /c:"\\build\\" /c:"\.idea\\" /c:"\.vscode\\" >nul 2>&1
    if !errorlevel! == 0 (
        set "skip_file=1"
        set "skip_reason=excluded directory"
    )
    
    rem Skip generated Tailwind CSS file (remove $ as findstr doesn't support full regex)
    echo !filepath! | findstr /i "\\assets\\css\\tailwind.css" >nul 2>&1
    if !errorlevel! == 0 (
        set "skip_file=1"
        set "skip_reason=generated Tailwind CSS"
    )
    
    if "!skip_file!"=="0" (
        rem Check if file still exists and is readable
        if exist "%%f" (
            echo. >> "%TEMP_FILE%"
            echo ========================================== >> "%TEMP_FILE%"
            echo File: %%f >> "%TEMP_FILE%"
            echo ========================================== >> "%TEMP_FILE%"
            echo. >> "%TEMP_FILE%"
            
            rem Type file with error handling
            type "%%f" >> "%TEMP_FILE%" 2>nul
            if errorlevel 1 (
                echo ERROR: Could not read file: %%f >> "%TEMP_FILE%"
            )
            echo. >> "%TEMP_FILE%"
            
            set /a "TOTAL_FILES+=1"
            set /a "TOTAL_SIZE+=file_size"
            echo Copied: %%~nxf ^(!file_size! bytes^)
        ) else (
            rem File no longer exists
            set "skip_file=1"
            set "skip_reason=file no longer exists"
        )
    )
)

echo.
echo ==========================================
echo Summary:
echo ==========================================
echo Total files copied: !TOTAL_FILES!
echo Total size copied: !TOTAL_SIZE! bytes
echo.

rem Copy to clipboard using Windows clip.exe (handles large files well)
type "%TEMP_FILE%" | clip 2>nul
if errorlevel 1 (
    echo ERROR: Failed to copy to clipboard using clip.exe
    echo Trying PowerShell as fallback...
    powershell -command "Get-Content -Path '%TEMP_FILE%' -Raw | Set-Clipboard" 2>nul
    if errorlevel 1 (
        echo ERROR: Failed both clip.exe and PowerShell
        echo File saved to: %TEMP_FILE%
        echo Total files: !TOTAL_FILES!
        echo You can manually open and copy from this file.
        goto end_clipboard
    )
)
echo Done! All code files have been copied to clipboard.
del "%TEMP_FILE%" 2>nul
goto end_clipboard

:end_clipboard

endlocal