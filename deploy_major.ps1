# Major deployment script — runs regression tests before deploying.
# Use this when bumping the minor or major version number.
# For patch-only deploys (e.g. v3.1.x -> v3.1.y) use gcloud directly.

Write-Host "Running calculation regression tests..."
python test_calculations.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Tests FAILED. Deployment aborted." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "All tests passed. Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy eve-valuation-engine --source . --region us-central1 --platform managed --quiet
