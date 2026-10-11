@echo off
title GoldenNugget Launcher
python main_app.py
if errorlevel 1 (
    echo.
    echo Error launching GoldenNugget.
    pause
)