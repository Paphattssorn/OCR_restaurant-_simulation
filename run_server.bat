@echo off
chcp 65001 > nul
title Vietnam OCR Classroom Server
echo =======================================================
echo   กำลังเริ่มต้นเซิร์ฟเวอร์สื่อการสอน OCR อาหารเวียดนาม...
echo =======================================================
echo.
echo [1] เปิดเบราว์เซอร์หน้าจออาจารย์ (http://localhost:8080)
start http://localhost:8080
echo [2] เริ่มต้น Python Server...
python server.py
pause
