@echo off
chcp 65001 >nul
title Eğitim PDF Atölyesi - Çevrimdışı
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (set "PY=py -3.11") else (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 veya ustunu onceden kurun.
  echo Bu baslatici internete baglanmaz ve paket indirmez.
  pause
  exit /b 1
)
%PY% app.py
pause
