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
JOB_NAME="eve-account-lifecycle"
CLOUDSQL_INSTANCE="eve-solutions-482317:us-central1:eve-db"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/eve-valuation-engine"

echo "─── Building image via Cloud Build + Kaniko cache ───────────────────────"
gcloud builds submit \
    --config cloudbuild.yaml \
    --project "$PROJECT_ID" \
    --quiet

echo ""
echo "─── Deploying $SERVICE (prod web) ───────────────────────────────────────"
# --min-instances=1 keeps one instance always warm so the first visitor after
# an idle period never waits on a cold start (Python + Streamlit + GDAL boot).
# Combined with the existing maxScale=1 (PDF/session-affinity workaround) this
# means exactly one always-on instance. Trade-off: ~a few $/month idle billing.
# Staging intentionally stays at min=0 (IAM-locked, rarely idle-critical).
gcloud run deploy "$SERVICE" \
    --image "${IMAGE_NAME}:latest" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --min-instances=1 \
    --quiet

# Force 100% traffic to the freshly-built revision. Belt-and-braces:
# `gcloud run deploy` normally routes traffic automatically, BUT if a
# previous run had explicitly pinned traffic (e.g. an `update-traffic
# --to-revisions=...=100` for a rollback), new revisions stay at 0%
# until traffic is explicitly shifted. This bit us on 2026-05-28
# after the v3.8.22 rollback. `--to-latest` is a safe no-op when
# traffic is already on the new revision.
echo ""
echo "─── Deploying $JOB_NAME (lifecycle) ─────────────────────────────"
# The prod Job runs from the same image as the service and must be
# redeployed with it — it was left out of this script until 2026-09-09,
# so the nightly lifecycle pass could quietly run weeks-old code. It now
# also carries the SMTP canary feeding the "EVE — email sending is broken"
# alert, which is worth nothing if the Job never picks up a new image.
# Mirrors the block in deploy_staging.sh.
gcloud run jobs deploy "$JOB_NAME" \
    --image "${IMAGE_NAME}:latest" \
    --region "$REGION" --project "$PROJECT_ID" \
    --command=python \
    --args=-m,scripts.check_unverified \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --task-timeout=300 \
    --max-retries=1 \
    --quiet

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
