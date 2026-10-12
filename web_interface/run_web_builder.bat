@echo off
cd %~dp0
cd ..
echo Starting Web Embed Builder...
echo.
echo Make sure your .env file is configured with:
echo - DISCORD_TOKEN
echo - WEB_USERNAME
echo - WEB_PASSWORD
echo.
echo Web interface will be available at: http://localhost:5000
echo.
python web_interface\web_embed_builder.py
pause
