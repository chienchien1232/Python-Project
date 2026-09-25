$healthUrl = 'http://localhost:8520/_stcore/health'
$appUrl = 'http://localhost:8520'

for ($attempt = 0; $attempt -lt 120; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 1
        if ($response.StatusCode -eq 200) {
            Start-Process $appUrl
            exit 0
        }
    } catch {
        # Streamlit is still starting; check again shortly.
    }
    Start-Sleep -Milliseconds 500
}
