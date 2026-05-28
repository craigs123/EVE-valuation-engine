#!/usr/bin/env bash
# Ongoing prod deploys.
#
# Mirrors scripts/deploy_staging.sh — same Kaniko build with
# registry-backed layer caching via cloudbuild.yaml, then deploys the
# resulting image to the prod Cloud Run service. The image tag and
# cache repo are shared with staging so deps installed during a staging
# build also speed up the next prod build (and vice-versa).
#
# Typical workflow:
#   git checkout main
#   git merge --no-ff staging -m "Merge staging into main for vX.Y.Z beta prod release"
#   bump version in app.py + utils/auth.py if not already bumped on staging
#   git push origin main
#   bash scripts/deploy_prod.sh
#
# Schema changes: run Alembic against the prod DB BEFORE this script
# (see memory/reference_local_migration.md).

set -euo pipefail

PROJECT_ID="eve-solutions-482317"
REGION="us-central1"
SERVICE="eve-valuation-engine"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/eve-valuation-engine"

echo "─── Building image via Cloud Build + Kaniko cache ───────────────────────"
gcloud builds submit \
    --config cloudbuild.yaml \
    --project "$PROJECT_ID" \
    --quiet

echo ""
echo "─── Deploying $SERVICE (prod web) ───────────────────────────────────────"
gcloud run deploy "$SERVICE" \
    --image "${IMAGE_NAME}:latest" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --quiet

# Force 100% traffic to the freshly-built revision. Belt-and-braces:
# `gcloud run deploy` normally routes traffic automatically, BUT if a
# previous run had explicitly pinned traffic (e.g. an `update-traffic
# --to-revisions=...=100` for a rollback), new revisions stay at 0%
# until traffic is explicitly shifted. This bit us on 2026-05-28
# after the v3.8.22 rollback. `--to-latest` is a safe no-op when
# traffic is already on the new revision.
echo ""
echo "─── Routing 100% traffic to latest revision ─────────────────────────────"
gcloud run services update-traffic "$SERVICE" \
    --to-latest \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --quiet

PROD_URL=$(gcloud run services describe "$SERVICE" \
    --region "$REGION" --project "$PROJECT_ID" \
    --format='value(status.url)')
echo ""
echo "Prod is live at: $PROD_URL"
