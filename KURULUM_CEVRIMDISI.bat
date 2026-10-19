@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Eğitim PDF Atölyesi - Çevrimdışı Kurulum
echo ==============================================================
echo Eğitim PDF Atölyesi - ÇEVRİMDIŞI KURULUM
echo ==============================================================
where py >nul 2>nul
if errorlevel 1 (echo Python Launcher bulunamadı. Python 3.11 kurun.& pause & exit /b 1)
set "ARCH="
py -3.11 -c "import struct,sys; print('64' if struct.calcsize('P')*8==64 else '32')" > "%TEMP%\egitim_pdf_arch.txt" 2>nul
if errorlevel 1 (echo Python 3.11 çalıştırılamadı.& pause & exit /b 1)
set /p ARCH=<"%TEMP%\egitim_pdf_arch.txt"
del "%TEMP%\egitim_pdf_arch.txt" >nul 2>nul
if "%ARCH%"=="64" (set "WHEELDIR=wheelhouse\win_amd64_py311") else (set "WHEELDIR=wheelhouse\win32_py311")
if not exist "%WHEELDIR%" (echo HATA: %WHEELDIR% klasörü yok. Önce HAZIRLA_CEVRIMDISI.bat çalıştırın.& pause & exit /b 1)
if not exist "%WHEELDIR%\*.whl" (echo HATA: %WHEELDIR% içinde wheel dosyası bulunamadı.& pause & exit /b 1)
echo Python mimarisi: %ARCH%-bit
echo Paket kaynağı: %WHEELDIR%
py -3.11 -m pip install --no-index --find-links="%WHEELDIR%" -r requirements.txt
if errorlevel 1 (echo HATA: Python paket kurulumu başarısız. Wheelhouse içeriğini ve Python sürümünü kontrol edin.& pause & exit /b 1)
py -3.11 -c "import reportlab,pypdf,docx,pptx,PIL,pytesseract; print('Python bağımlılıkları OK')"
if errorlevel 1 (echo HATA: Kurulum sonrası bağımlılık doğrulaması başarısız.& pause & exit /b 1)
if "%ARCH%"=="64" (
  if not exist "ocr_installer\tesseract-ocr-w64-setup-5.4.0.20240606.exe" (echo UYARI: Tesseract kurucusu bulunamadı. Uygulama OCR olmadan çalışabilir.& goto startapp)
  echo Tesseract OCR kurulum penceresi açılacak. Kurulumda tur/eng/osd dil dosyaları bu paketten kopyalanacaktır.
  start /wait "Tesseract OCR" "ocr_installer\tesseract-ocr-w64-setup-5.4.0.20240606.exe"
  set "TESS=C:\Program Files\Tesseract-OCR"
  if not exist "C:\Program Files\Tesseract-OCR\tessdata" set "TESS=%LOCALAPPDATA%\Programs\Tesseract-OCR"
  if exist "!TESS!\tessdata" (
    for %%L in (tur eng osd) do if exist "ocr_installer\%%L.traineddata" copy /Y "ocr_installer\%%L.traineddata" "!TESS!\tessdata\%%L.traineddata" >nul
    setx TESSDATA_PREFIX "!TESS!\tessdata" >nul
  ) else echo UYARI: Tesseract kurulum klasörü bulunamadı; OCR'ı ayrıca yapılandırın.
) else (
  echo UYARI: Bu paket Tesseract OCR için x64 kurucu içerir; Windows x86'daki OCR otomatik kurulmayacaktır.
)
:startapp
echo.
echo Kurulum/doğrulama tamamlandı. Uygulamayı başlatmak için baslat.bat çalıştırın.
pause
