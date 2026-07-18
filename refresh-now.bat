@echo off
rem Trigger the GitHub Actions playlist refresh immediately and wait for it.
set GH="C:\Program Files\GitHub CLI\gh.exe"
echo Triggering refresh workflow...
%GH% workflow run refresh.yml -R ShitijDutta/tvstream || goto :err
echo Waiting for run to finish (usually 2-3 minutes)...
timeout /t 15 /nobreak >nul
for /f "usebackq delims=" %%i in (`%GH% run list -R ShitijDutta/tvstream --limit 1 --json databaseId --jq ".[0].databaseId"`) do set RUNID=%%i
%GH% run watch %RUNID% -R ShitijDutta/tvstream --exit-status && echo DONE - now update the playlist in OTT Navigator on the TV. || echo Run failed - check github.com/ShitijDutta/tvstream/actions
pause
exit /b
:err
echo Could not trigger workflow. Are you logged in? Try: gh auth login
pause
