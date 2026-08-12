@echo off
REM Demarrage du tableau de bord - Windows.
REM
REM Equivalent de demarrer.sh : cherche Python, lance le diagnostic, puis
REM demarre Streamlit uniquement si le diagnostic est vert. N'installe rien
REM sans confirmation.

setlocal
cd /d "%~dp0"

echo.
echo   Acces a l'eau potable au Togo
echo   Data Challenge Environnement . Eau et hydraulique
echo.

REM --- 1. Trouver Python -----------------------------------------------------
REM L'environnement virtuel du projet prime, puis le lanceur "py", puis python.

set "PYTHON="

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo   Environnement virtuel du projet detecte ^(.venv^)
    goto :trouve
)

py -3 -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py -3"
    goto :trouve
)

python -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
    goto :trouve
)

echo   Python 3.9 ou plus recent est introuvable sur cette machine.
echo.
echo   A faire :
echo     - installer depuis https://www.python.org/downloads/
echo     - cocher "Add Python to PATH" pendant l'installation
echo.
echo   Puis relancez : demarrer.bat
echo.
pause
exit /b 1

:trouve
for /f "delims=" %%v in ('%PYTHON% -V 2^>^&1') do echo   Python utilise : %%v

REM --- 2. Diagnostic ---------------------------------------------------------

%PYTHON% verifier.py
if not errorlevel 1 goto :lancer

echo.
echo   Le diagnostic signale des manques. Installer les bibliotheques
echo   maintenant ? Cela lancera :
echo.
echo     %PYTHON% -m pip install -r requirements.txt
echo.
set /p REPONSE="  Installer ? [o/N] "

if /i "%REPONSE%"=="o" goto :installer
if /i "%REPONSE%"=="y" goto :installer

echo.
echo   Rien n'a ete installe. Relancez demarrer.bat quand vous serez pret.
echo.
pause
exit /b 1

:installer
echo.
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo   L'installation a echoue. Essayez dans un environnement virtuel :
    echo     %PYTHON% -m venv .venv
    echo     .venv\Scripts\activate
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo   Nouveau diagnostic :
%PYTHON% verifier.py
if errorlevel 1 (
    pause
    exit /b 1
)

REM --- 3. Lancement ----------------------------------------------------------

:lancer
echo.
echo   Lancement du tableau de bord...
echo   Une fois le navigateur ouvert : zoom 75%%, largeur ^>= 1440 px.
echo   Pour arreter : Ctrl+C dans cette fenetre.
echo.

%PYTHON% -m streamlit run app.py
