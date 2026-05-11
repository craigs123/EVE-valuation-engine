# One-time DB setup for the staging environment.
#
# 1. Authorize this machine's IP on Cloud SQL eve-db (temporary, revoked at the end).
# 2. Create the `eve_staging` database on the shared instance (idempotent).
# 3. Run Alembic migrations against `eve_staging` to build the schema.
# 4. Revoke the IP authorization.
#
# Mirrors the prod migration flow in reference_local_migration.md but targets
# a different database name on the same instance. Re-running is safe: the
# CREATE DATABASE is idempotent, `alembic upgrade head` is idempotent.

$ErrorActionPreference = 'Stop'
$projectId = 'eve-solutions-482317'

Write-Host '--- 1. Getting public IP and authorizing on Cloud SQL ---'
$ip = (Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content
Write-Host "IP: $ip"
gcloud sql instances patch eve-db --authorized-networks="$ip/32" --project=$projectId --quiet
if ($LASTEXITCODE -ne 0) { throw 'Failed to authorize IP on eve-db' }

try {
    Write-Host ''
    Write-Host '--- 2. Creating eve_staging database (idempotent) ---'
    python scripts/create_staging_db.py
    if ($LASTEXITCODE -ne 0) { throw 'create_staging_db.py failed' }

    Write-Host ''
    Write-Host '--- 3. Running Alembic migrations against eve_staging ---'
    $env:DATABASE_URL = 'postgresql+psycopg2://neondb_owner:N1Hdp7-v4QvOZ8HqvqNqDHGOWIX5-lZB@136.114.114.44/eve_staging'
    python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'alembic upgrade head failed' }
}
finally {
    Write-Host ''
    Write-Host '--- 4. Revoking IP authorization (always runs) ---'
    gcloud sql instances patch eve-db --clear-authorized-networks --project=$projectId --quiet
}

Write-Host ''
Write-Host 'Staging DB ready. Next step: run `bash scripts/setup_staging.sh` to create the Cloud Run service, Job and Scheduler.'
