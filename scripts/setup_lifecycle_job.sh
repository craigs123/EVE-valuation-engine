#!/usr/bin/env bash
# One-time setup for the daily unverified-account lifecycle job.
#
# Creates / updates:
#   - Cloud Run Job  : `eve-account-lifecycle`
#     Same Docker image as the web service, with the entrypoint overridden to
#     `python -m scripts.check_unverified`. Inherits env vars and Cloud SQL
#     connection from the web service so it talks to the same DB.
#   - Cloud Scheduler: `eve-account-lifecycle-daily`
#     Fires once per day at 02:00 UTC and triggers the Job over HTTP.
#
# Prereqs (run once if not already done):
#   gcloud services enable run.googleapis.com cloudscheduler.googleapis.com
#   gcloud auth application-default login
#
# After this script runs, manually verify with:
#   gcloud run jobs describe eve-account-lifecycle --region us-central1
#   gcloud scheduler jobs describe eve-account-lifecycle-daily --location us-central1
#
# To run the job on demand for testing:
#   gcloud run jobs execute eve-account-lifecycle --region us-central1 --wait

set -euo pipefail

PROJECT_ID="eve-solutions-482317"
REGION="us-central1"
SERVICE="eve-valuation-engine"
JOB_NAME="eve-account-lifecycle"
SCHEDULER_NAME="eve-account-lifecycle-daily"
SCHEDULE="0 2 * * *"        # 02:00 UTC daily
TIME_ZONE="UTC"

# Service account used by Scheduler to invoke the Job. The default Compute SA
# already has run.invoker on the project; using it keeps setup minimal.
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
INVOKER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

CLOUDSQL_INSTANCE="eve-solutions-482317:us-central1:eve-db"

echo "─── Reading env vars from current web service ───────────────────────────"
# Pull env vars from the live service and write them to a temp YAML file.
# Using --env-vars-file avoids all the delimiter-escaping headaches that come
# with --set/--update-env-vars when values contain '@', ',', or '/'.
ENV_FILE=$(mktemp --suffix=.yaml)
trap 'rm -f "$ENV_FILE"' EXIT

gcloud run services describe "$SERVICE" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format='json(spec.template.spec.containers[0].env)' \
    | python -c "
import sys, json, yaml
env = (json.load(sys.stdin).get('spec', {}).get('template', {})
       .get('spec', {}).get('containers', [{}])[0].get('env') or [])
pairs = {e['name']: e.get('value', '') for e in env if 'name' in e and 'value' in e}
print(yaml.safe_dump(pairs, default_flow_style=False, allow_unicode=True))
" > "$ENV_FILE" 2>/dev/null || true

if [[ ! -s "$ENV_FILE" ]]; then
    echo "WARNING: could not read env vars from service $SERVICE."
    echo "         Job will be deployed without env vars; set them manually after."
fi

echo "─── Creating / updating Cloud Run Job: $JOB_NAME ────────────────────────"
# `deploy` is idempotent: creates if missing, updates if it exists.
gcloud run jobs deploy "$JOB_NAME" \
    --source . \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --command=python \
    --args=-m,scripts.check_unverified \
    --set-cloudsql-instances "$CLOUDSQL_INSTANCE" \
    --task-timeout=300 \
    --max-retries=1 \
    --quiet

if [[ -s "$ENV_FILE" ]]; then
    echo ""
    echo "─── Copying env vars from web service to Job ────────────────────────────"
    gcloud run jobs update "$JOB_NAME" \
        --region "$REGION" \
        --project "$PROJECT_ID" \
        --env-vars-file "$ENV_FILE" \
        --quiet
    echo "Env vars copied across."
fi
echo ""

JOB_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

echo "─── Creating / updating Cloud Scheduler: $SCHEDULER_NAME ───────────────"
# Delete the existing scheduler entry first so the create is idempotent.
gcloud scheduler jobs delete "$SCHEDULER_NAME" \
    --location "$REGION" \
    --project "$PROJECT_ID" \
    --quiet 2>/dev/null || true

gcloud scheduler jobs create http "$SCHEDULER_NAME" \
    --location "$REGION" \
    --project "$PROJECT_ID" \
    --schedule "$SCHEDULE" \
    --time-zone "$TIME_ZONE" \
    --uri "$JOB_URI" \
    --http-method POST \
    --oauth-service-account-email "$INVOKER_SA"

echo ""
echo "─── Done ────────────────────────────────────────────────────────────────"
echo "Cloud Run Job:  $JOB_NAME (region $REGION)"
echo "Scheduler:      $SCHEDULER_NAME (daily at $SCHEDULE $TIME_ZONE)"
echo ""
echo "Next steps:"
echo "  1. Run the env-var update command above to wire DB + email creds."
echo "  2. Test once: gcloud run jobs execute $JOB_NAME --region $REGION --wait"
echo "  3. Check logs: gcloud run jobs executions list --job $JOB_NAME --region $REGION"
