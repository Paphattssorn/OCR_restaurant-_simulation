@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Vietnam OCR Classroom Server

echo =======================================================
echo   กำลังเริ่มต้นเซิร์ฟเวอร์สื่อการสอน OCR อาหารเวียดนาม...
echo =======================================================
echo.

:: เช็คและปิด process เก่าที่ค้างในพอร์ต 8080 (ถ้ามี)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING 2^>nul') do (
    echo [INFO] พบโปรเซสเดิมค้างที่พอร์ต 8080 (PID: %%a) กำลังปิดให้อัตโนมัติ...
    taskkill /f /pid %%a > nul 2>&1
)

:: ตรวจสอบว่ามีคำสั่ง Python หรือไม่
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ไม่พบคำสั่ง Python ในระบบ!
    echo กรุณาตรวจสอบว่าได้ติดตั้ง Python แล้วหรือยัง
    echo หรือพิมพ์ python ในหน้าต่างนี้เพื่อดูข้อผิดพลาด
    echo.
    pause
    exit /b 1
)

echo [1] เปิดหน้าจออาจารย์ในเบราว์เซอร์: http://localhost:8080
start http://localhost:8080

echo [2] สตาร์ท Python Server บนพอร์ต 8080...
echo -------------------------------------------------------
echo  (หากต้องการปิดเซิร์ฟเวอร์ ให้กดปิดหน้าต่างดำนี้ หรือกด Ctrl + C)
echo -------------------------------------------------------
echo.
python server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] เกิดข้อผิดพลาดในการรัน server.py
    pause
)
