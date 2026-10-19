@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Eğitim PDF Atölyesi - Kurulum Kontrolü
where py >nul 2>nul
if errorlevel 1 (echo Python Launcher bulunamadı.& pause & exit /b 1)
echo === Python ===
py -3.11 --version
echo.
echo === Python bağımlılıkları ===
py -3.11 -c "import reportlab,pypdf,docx,pptx,PIL,pytesseract; print('OK: reportlab, pypdf, python-docx, python-pptx, Pillow, pytesseract')"
if errorlevel 1 echo HATA: Bir veya daha fazla Python paketi eksik.
echo.
echo === Tesseract ===
where tesseract >nul 2>nul
if errorlevel 1 (
 echo Tesseract PATH üzerinde bulunamadı. Varsayılan kurulum klasörünü kontrol edin.
 if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
) else (
 tesseract --version
 tesseract --list-langs
)
echo.
echo Kontrol tamamlandı. Yukarıdaki hata ve uyarıları inceleyin.
pause
