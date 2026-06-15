$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Project ".venv\Scripts\python.exe"
$Main = Join-Path $Project "main.py"
$WatchdogLog = Join-Path $Project "watchdog.log"
$ProjectPattern = "*" + ($Project -replace "\\", "*") + "*"

Set-Location $Project

function Write-WatchdogLog($Message) {
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Write-Host $Line
    Add-Content -Path $WatchdogLog -Value $Line -Encoding UTF8
}

function Stop-OldBotCopies {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $PID -and
            $_.Name -like "*python*" -and
            ($_.CommandLine -like "*telegram-bot*" -or $_.CommandLine -like $ProjectPattern) -and
            ($_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*bot.py*")
        } |
        ForEach-Object {
            Write-WatchdogLog "Stopping old bot process PID=$($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force
        }
}

Write-WatchdogLog "Watchdog started"
Stop-OldBotCopies
Start-Sleep -Seconds 3

while ($true) {
    Write-WatchdogLog "Starting bot"
    & $Python $Main
    $ExitCode = $LASTEXITCODE
    Write-WatchdogLog "Bot stopped with exit code $ExitCode. Restart in 5 seconds."
    Start-Sleep -Seconds 5
    Stop-OldBotCopies
}
