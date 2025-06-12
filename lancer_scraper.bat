@echo off
echo ---------------------------------------------
echo    LANCEMENT DU SCRAPER HELLOWORK
echo ---------------------------------------------
echo.

:: Vérifier si Python est installé
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo et cocher l'option "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

:: Lancer le script Python
echo Lancement du scraper HelloWork...
echo.
python lancer_scraper.py

:: En cas d'erreur
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Une erreur s'est produite lors de l'exécution du script.
    pause
)

exit /b
