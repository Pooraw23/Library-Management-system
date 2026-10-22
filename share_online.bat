@echo off
title Smart Library - Share Online Link
echo ========================================================
echo   Generating Free Public Link for WhatsApp / Friends...
echo ========================================================
echo.
echo NOTE: Make sure "run.bat" is running in another window!
echo.
echo Generating public HTTPS link...
echo (Copy the https:// link shown below and send it on WhatsApp!)
echo ========================================================
echo.
ssh -p 443 -R0:localhost:5000 a.pinggy.io
pause
