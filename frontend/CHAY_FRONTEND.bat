@echo off
chcp 65001 >nul
color 0C
title Frontend Server - Port 8000
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           KHỞI ĐỘNG FRONTEND SERVER                      ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo [ℹ]  Frontend sẽ chạy tại: http://localhost:8000
echo [⚠]  Đảm bảo Backend đã chạy tại http://localhost:5000
echo.
echo ═══════════════════════════════════════════════════════════
echo.

cd /d %~dp0
echo [ℹ]  Frontend Server đang chạy:
echo      - Local: http://localhost:8000
echo      - LAN:   http://192.168.1.4:8000
echo.
python -m http.server 8000 --bind 0.0.0.0

pause

