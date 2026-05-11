#!/usr/bin/env bash
# One-time setup for the staging environment's Cloud Run resources.
#
# Creates / updates:
#   - Cloud Run service:  eve-valuation-engine-staging
#   - Cloud Run Job:      eve-account-lifecycle-staging
#   - Cloud Scheduler:    eve-account-lifecycle-staging-daily (03:00 UTC)
#
# Env vars are copied from the production service, but DATABASE_URL is
# rewritten to point at the `eve_staging` database (must already exist —
# see scripts/setup_staging_db.ps1) and APP_BASE_URL is rewritten to the
# staging service's own URL.
#
# Run AFTER scripts/setup_staging_db.ps1 has created and migrated the
# staging database. Re-running is idempotent (gcloud deploy creates or
# updates; scheduler is deleted then recreated).

set -euo pipefail

PROJECT_ID="eve-solutions-482317"
REGION="us-central1"

PROD_SERVICE="eve-valuation-engine"
SERVICE="eve-valuation-engine-staging"
JOB_NAME="eve-account-lifecycle-staging"
SCHEDULER_NAME="eve-account-lifecycle-staging-daily"
SCHEDULE="0 3 * * *"   # 03:00 UTC daily — 1h offset from prod (02:00 UTC)
TIME_ZONE="UTC"

CLOUDSQL_INSTANCE="eve-solutions-482317:us-central1:eve-db"

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
INVOKER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "─── 1. Deploying staging Cloud Run service ──────────────────────────────"
gcloud run deploy "$SERVICE" \
    --source . \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --platform managed \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --allow-unauthenticated \
    --quiet

STAGING_URL=$(gcloud run services describe "$SERVICE" \
    --region "$REGION" --project "$PROJECT_ID" \
    --format='value(status.url)')
echo "Staging URL: $STAGING_URL"

echo ""
echo "─── 2. Building staging env-vars file (DATABASE_URL → eve_staging) ─────"
ENV_FILE=$(mktemp --suffix=.yaml)
trap 'rm -f "$ENV_FILE"' EXIT

gcloud run services describe "$PROD_SERVICE" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format='json(spec.template.spec.containers[0].env)' \
    | STAGING_URL_FOR_PY="$STAGING_URL" python -c "
import os, sys, json
env = (json.load(sys.stdin).get('spec', {}).get('template', {})
       .get('spec', {}).get('containers', [{}])[0].get('env') or [])
staging_url = os.environ['STAGING_URL_FOR_PY']
seen = set()
for e in env:
    if 'name' not in e or 'value' not in e:
        continue
    name = e['name']
    v = e['value']
    if name == 'DATABASE_URL':
        # Repoint at the staging database on the same instance.
        v = v.replace('/neondb?', '/eve_staging?').replace('/neondb', '/eve_staging')
    elif name == 'APP_BASE_URL':
        v = staging_url
    seen.add(name)
    v_esc = str(v).replace(chr(39), chr(39)+chr(39))
    print(f\"{name}: '{v_esc}'\")
# Ensure APP_BASE_URL is set even if prod didn't have one.
if 'APP_BASE_URL' not in seen:
    print(f\"APP_BASE_URL: '{staging_url}'\")
" > "$ENV_FILE"

echo "Env file contents:"
sed 's/password.*/password: *****/I; s/secret.*/secret: *****/I' "$ENV_FILE"

echo ""
echo "─── 3. Applying env vars to staging service ────────────────────────────"
gcloud run services update "$SERVICE" \
    --region "$REGION" --project "$PROJECT_ID" \
    --env-vars-file "$ENV_FILE" \
    --quiet

echo ""
echo "─── 4. Creating / updating Cloud Run Job: $JOB_NAME ─────────────────────"
gcloud run jobs deploy "$JOB_NAME" \
    --source . \
    --region "$REGION" --project "$PROJECT_ID" \
    --command=python \
    --args=-m,scripts.check_unverified \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --task-timeout=300 \
    --max-retries=1 \
    --quiet

echo ""
echo "─── 5. Applying env vars to Job ────────────────────────────────────────"
gcloud run jobs update "$JOB_NAME" \
    --region "$REGION" --project "$PROJECT_ID" \
    --env-vars-file "$ENV_FILE" \
    --quiet

echo ""
echo "─── 6. Creating Cloud Scheduler: $SCHEDULER_NAME ───────────────────────"
JOB_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

gcloud scheduler jobs delete "$SCHEDULER_NAME" \
    --location "$REGION" --project "$PROJECT_ID" \
    --quiet 2>/dev/null || true

gcloud scheduler jobs create http "$SCHEDULER_NAME" \
    --location "$REGION" --project "$PROJECT_ID" \
    --schedule "$SCHEDULE" --time-zone "$TIME_ZONE" \
    --uri "$JOB_URI" --http-method POST \
    --oauth-service-account-email "$INVOKER_SA"

echo ""
echo "─── Done ────────────────────────────────────────────────────────────────"
echo "Staging service:    $STAGING_URL"
echo "Lifecycle Job:      $JOB_NAME (region $REGION)"
echo "Scheduler:          $SCHEDULER_NAME (daily $SCHEDULE $TIME_ZONE)"
echo ""
echo "Test the Job once:  gcloud run jobs execute $JOB_NAME --region $REGION --wait"
echo "Ongoing staging deploys: bash scripts/deploy_staging.sh"
