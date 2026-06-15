$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Project ".venv\Scripts\python.exe"
$Main = Join-Path $Project "main.py"
$OutLog = Join-Path $Project "bot.out.log"
$ErrLog = Join-Path $Project "bot.err.log"

Get-CimInstance Win32_Process |
    Where-Object {
        $_.ProcessId -ne $PID -and
        $_.Name -like "*python*" -and
        $_.CommandLine -like "*PycharmProjects*telegram-bot*" -and
        ($_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*bot.py*")
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
    }

Start-Process `
    -FilePath $Python `
    -ArgumentList @($Main) `
    -WorkingDirectory $Project `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog
