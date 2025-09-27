@echo off
chcp 65001
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Running the script...
python merger.py

echo.
echo Script finished. Press any key to exit.
pause