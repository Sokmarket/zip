@echo off
chcp 65001 >nul
setlocal
title Eğitim PDF Atölyesi - Yerel Ağ Modu
cd /d "%~dp0"
echo UYARI: Bu mod uygulamayı aynı yerel ağdaki cihazlara açar.
echo Yalnızca güvendiğiniz özel Wi-Fi ağında kullanın; herkese açık Wi-Fi'da çalıştırmayın.
echo Ağdaki diğer kişiler dosya yükleyebilir ve çıktı oluşturabilir.
echo Windows Güvenlik Duvarı 8767/TCP erişim izni sorabilir.
echo.
set "EGITIM_HOST=0.0.0.0"
where py >nul 2>nul
if not errorlevel 1 (py -3.11 app.py) else (python app.py)
pause
