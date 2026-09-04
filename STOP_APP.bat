@echo off
setlocal enabledelayedexpansion

title SIH26188 - Stop Services

echo =========================================================================
echo   SIH26188: Stopping Screening System Services
echo =========================================================================
echo.

echo [*] Closing SIH26188 terminal windows...
taskkill /F /FI "WINDOWTITLE eq SIH26188*" 2>nul

echo [*] Terminating lingering servers on port 8000 (Backend) and port 5173 (Frontend)...
powershell -Command "
$ports = @(8000, 5173);
foreach ($p in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue;
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique;
        foreach ($procId in $pids) {
            if ($procId -gt 0) {
                Write-Host ('Killing process ' + $procId + ' on port ' + $p);
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue;
            }
        }
    }
}
"

echo.
echo [OK] All backend and frontend screening services have been stopped.
echo.
pause
