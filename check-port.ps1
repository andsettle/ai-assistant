$conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($c in $conns) {
        if ($c.OwningProcess -ne 0) {
            Write-Host "Killing PID $($c.OwningProcess)"
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "Port 8000 is free"
}
