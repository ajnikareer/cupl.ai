#!/usr/bin/env bash
# Deploy backend (API + WeaveWed MCP server + voice WebSocket) to Cloud Run.
#   PROJECT=.. REGION=asia-south1 WEB_ORIGIN=https://<project>.web.app QLOO_BASE_URL=https://... bash infra/deploy_api.sh
set -euo pipefail
: "${PROJECT:?}"; : "${WEB_ORIGIN:?}"; REGION="${REGION:-asia-south1}"
SA="weavewed-api@${PROJECT}.iam.gserviceaccount.com"
cd "$(dirname "$0")/../backend"
ENV="APP_ENV=live,GCP_PROJECT=${PROJECT},VERTEX_LOCATION=${VERTEX_LOCATION:-us-central1},ALLOWED_ORIGINS=${WEB_ORIGIN},APP_PUBLIC_URL=${WEB_ORIGIN}"
ENV+=",GEMINI_LIVE_MODEL=${GEMINI_LIVE_MODEL:-gemini-live-2.5-flash-native-audio},GEMINI_AGENT_MODEL=${GEMINI_AGENT_MODEL:-gemini-2.5-flash}"
ENV+=",GEMINI_PLANNER_MODEL=${GEMINI_PLANNER_MODEL:-gemini-2.5-pro},GEMINI_FAST_MODEL=${GEMINI_FAST_MODEL:-gemini-2.5-flash}"
ENV+=",QLOO_BASE_URL=${QLOO_BASE_URL:-https://hackathon.api.qloo.com},LIVE_VOICE_NAME=${LIVE_VOICE_NAME:-Aoede},AGENT_TOOL_TRANSPORT=mcp"
# --no-cpu-throttling: background plan builds & learning keep running after the response
# --timeout 3600 + --session-affinity: long voice WebSockets
# --min-instances 1: no cold start before a voice call
gcloud run deploy weavewed-api --source . --region "$REGION" --project "$PROJECT" --service-account "$SA" \
  --allow-unauthenticated --min-instances 1 --max-instances 10 --cpu 2 --memory 2Gi --timeout 3600 \
  --no-cpu-throttling --session-affinity --concurrency 60 \
  --set-secrets QLOO_API_KEY=qloo-key:latest,CRON_SECRET=cron-secret:latest,MCP_INTERNAL_TOKEN=mcp-internal-token:latest \
  --set-env-vars "$ENV"
URL=$(gcloud run services describe weavewed-api --region "$REGION" --format='value(status.url)')
echo "API: $URL   (MCP server: $URL/mcp/)"
CRON=$(gcloud secrets versions access latest --secret=cron-secret)
gcloud scheduler jobs create http weavewed-cron --location "$REGION" --schedule "*/15 * * * *" \
  --uri "$URL/internal/cron/run" --http-method POST --headers "X-Cron-Secret=$CRON" 2>/dev/null \
  || gcloud scheduler jobs update http weavewed-cron --location "$REGION" --schedule "*/15 * * * *" \
     --uri "$URL/internal/cron/run" --http-method POST --update-headers "X-Cron-Secret=$CRON"
echo "Deep health check:"; curl -s "$URL/healthz?deep=true" | python3 -m json.tool || true
