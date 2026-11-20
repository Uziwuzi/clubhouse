@echo off
rem Builds dist\Clubhouse (Clubhouse.exe + _internal) and dist\Clubhouse.zip. Run from anywhere.
cd /d "%~dp0.."
.venv\Scripts\python.exe packaging\make_icon.py || goto :fail
.venv\Scripts\python.exe -m PyInstaller packaging\clubhouse.spec --noconfirm --distpath dist --workpath build || goto :fail
copy /y packaging\README.txt dist\Clubhouse\README.txt >nul
copy /y CHANGELOG.md dist\Clubhouse\CHANGELOG.md >nul
powershell -NoProfile -Command "Compress-Archive -Path dist\Clubhouse -DestinationPath dist\Clubhouse.zip -Force"
echo Done: dist\Clubhouse\Clubhouse.exe and dist\Clubhouse.zip
goto :eof
:fail
echo Build failed.
exit /b 1
