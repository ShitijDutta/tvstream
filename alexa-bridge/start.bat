@echo off
rem Starts the TVStream Alexa bridge: local tuner server + fauxmo emulator.
rem Add this script to Task Scheduler (run at logon) for always-on voice control.
cd /d "%~dp0"
start "tvstream-tuner" cmd /c python tuner_server.py
start "tvstream-fauxmo" cmd /c fauxmo -c config.json -v
echo Bridge started (two windows: tuner server + fauxmo).
