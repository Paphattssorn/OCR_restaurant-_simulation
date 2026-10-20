@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Vietnam OCR Bistro - Online Cloud Launcher

echo =======================================================
echo   กำลังเริ่มต้นเซิร์ฟเวอร์แบบออนไลน์ (Cloudflare Public URL)
echo   รองรับนักเรียนที่ใช้ 4G/5G และข้าม Wi-Fi ได้ 100%%
echo =======================================================
echo.

python run_online.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] เกิดข้อผิดพลาดในการเชื่อมต่อ
    pause
)
