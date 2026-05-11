#!/usr/bin/env bash
# Ongoing staging deploys (after one-time setup via setup_staging_db.ps1 +
# setup_staging.sh).
#
# Rebuilds the Docker image from the current working tree and redeploys
# both the Cloud Run service and the lifecycle Job. Env vars and secrets
# already on the staging resources are preserved (no --set-env-vars).
#
# Typical workflow:
#   git checkout staging
#   <make changes / merge from feature branches>
#   bump version in app.py + utils/auth.py (e.g. v3.6.0-rc1)
#   git commit && git push origin staging
#   bash scripts/deploy_staging.sh
#   test on the staging URL
#   <when ready> open PR from staging → main, follow prod deploy flow

set -euo pipefail

PROJECT_ID="eve-solutions-482317"
REGION="us-central1"
SERVICE="eve-valuation-engine-staging"
JOB_NAME="eve-account-lifecycle-staging"
CLOUDSQL_INSTANCE="eve-solutions-482317:us-central1:eve-db"

echo "─── Deploying $SERVICE (web) ────────────────────────────────────────────"
gcloud run deploy "$SERVICE" \
    --source . \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --quiet

echo ""
echo "─── Deploying $JOB_NAME (lifecycle) ─────────────────────────────────────"
gcloud run jobs deploy "$JOB_NAME" \
    --source . \
    --region "$REGION" --project "$PROJECT_ID" \
    --command=python \
    --args=-m,scripts.check_unverified \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --task-timeout=300 \
    --max-retries=1 \
    --quiet

STAGING_URL=$(gcloud run services describe "$SERVICE" \
    --region "$REGION" --project "$PROJECT_ID" \
    --format='value(status.url)')
echo ""
echo "Staging is live at: $STAGING_URL"
