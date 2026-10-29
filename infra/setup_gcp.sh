#!/usr/bin/env bash
# One-time GCP setup for WeaveWed (live).
#   PROJECT=my-proj REGION=asia-south1 bash infra/setup_gcp.sh
set -euo pipefail
: "${PROJECT:?set PROJECT}"; REGION="${REGION:-asia-south1}"
gcloud config set project "$PROJECT"
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com cloudscheduler.googleapis.com identitytoolkit.googleapis.com
gcloud firestore databases create --location="$REGION" --type=firestore-native 2>/dev/null || echo "Firestore DB exists"
# Vector index for episodic memory (768 dims, pre-filtered by couple_id)
gcloud firestore indexes composite create --collection-group=episodes --query-scope=COLLECTION \
  --field-config=order=ASCENDING,field-path=couple_id \
  --field-config='vector-config={"dimension":"768","flat":"{}"},field-path=embedding' 2>/dev/null || echo "vector index exists/creating"
gcloud iam service-accounts create weavewed-api --display-name="WeaveWed API" 2>/dev/null || true
SA="weavewed-api@${PROJECT}.iam.gserviceaccount.com"
for ROLE in roles/aiplatform.user roles/datastore.user roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role="$ROLE" --quiet >/dev/null
done
put_secret () { printf "%s" "$2" | gcloud secrets create "$1" --data-file=- 2>/dev/null || printf "%s" "$2" | gcloud secrets versions add "$1" --data-file=-; }
read -rsp "QLOO API key: " QK; echo
put_secret qloo-key "$QK"
put_secret cron-secret "$(openssl rand -hex 24)"
put_secret mcp-internal-token "$(openssl rand -hex 32)"
echo "✅ Done. Secrets: qloo-key, cron-secret, mcp-internal-token. Service account: $SA"
