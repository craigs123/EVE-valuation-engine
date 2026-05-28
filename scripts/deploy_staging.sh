#!/usr/bin/env bash
# Ongoing staging deploys (after one-time setup via setup_staging_db.ps1 +
# setup_staging.sh).
#
# Builds the Docker image via Cloud Build + Kaniko (with registry-backed
# layer cache, see cloudbuild.yaml), then redeploys both the staging
# Cloud Run service and the lifecycle Job from the same image. Env vars
# and secrets already on the staging resources are preserved (no
# --set-env-vars).
#
# Switched off `gcloud run deploy --source` on 2026-05-28 because each
# code-only deploy was rebuilding all Python deps from scratch (~4–6
# min). Kaniko's layer cache drops that to ~60–90 s once the deps layer
# is warm.
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
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/eve-valuation-engine"

echo "─── Building image via Cloud Build + Kaniko cache ───────────────────────"
gcloud builds submit \
    --config cloudbuild.yaml \
    --project "$PROJECT_ID" \
    --quiet

echo ""
echo "─── Deploying $SERVICE (web) ────────────────────────────────────────────"
gcloud run deploy "$SERVICE" \
    --image "${IMAGE_NAME}:latest" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --quiet

echo ""
echo "─── Deploying $JOB_NAME (lifecycle) ─────────────────────────────────────"
gcloud run jobs deploy "$JOB_NAME" \
    --image "${IMAGE_NAME}:latest" \
    --region "$REGION" --project "$PROJECT_ID" \
    --command=python \
    --args=-m,scripts.check_unverified \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --task-timeout=300 \
    --max-retries=1 \
    --quiet

# Belt-and-braces — see the matching block in scripts/deploy_prod.sh.
echo ""
echo "─── Routing 100% traffic to latest revision ─────────────────────────────"
gcloud run services update-traffic "$SERVICE" \
    --to-latest \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --quiet

STAGING_URL=$(gcloud run services describe "$SERVICE" \
    --region "$REGION" --project "$PROJECT_ID" \
    --format='value(status.url)')
echo ""
echo "Staging is live at: $STAGING_URL"
