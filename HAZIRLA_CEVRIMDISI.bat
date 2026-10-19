@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Eğitim PDF Atölyesi - Çevrimdışı Paket Hazırlama
echo ==============================================================
echo Eğitim PDF Atölyesi - ÇEVRİMDIŞI PAKET HAZIRLAMA
echo ==============================================================
echo Bu işlem internet erişimli Windows bilgisayarda çalıştırılır.
echo Python 3.11 ve pip gereklidir. x64 ve x86 wheel klasörleri ayrı hazırlanır.
echo Tesseract OCR kurucusu ve tur/eng/osd dil verileri de indirilir.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo HATA: Python Launcher (py.exe) bulunamadı. Python 3.11 kurun.
  pause
  exit /b 1
)
py -3.11 --version >nul 2>nul
if errorlevel 1 (
  echo HATA: Python 3.11 bulunamadı. Python 3.11 x64 kurun.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0HAZIRLA_CEVRIMDISI.ps1"
if errorlevel 1 (
  echo.
  echo HAZIRLAMA TAMAMLANAMADI. Ekrandaki hataları kontrol edin.
  pause
  exit /b 1
)
echo.
echo Hazırlama betiği tamamlandı. RAPOR_HAZIRLIK.txt dosyasını kontrol edin.
pause
