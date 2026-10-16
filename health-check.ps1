Start-Sleep 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host $response.Content
} catch {
    Write-Host "ERROR: Backend not responding - $($_.Exception.Message)"
}
