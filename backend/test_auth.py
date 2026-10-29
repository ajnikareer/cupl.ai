import os
import subprocess
import google.auth
from google.oauth2.credentials import Credentials

token = subprocess.check_output("gcloud auth print-access-token", shell=True, text=True).strip()
print("Access token retrieved, length:", len(token))

creds = Credentials(token=token)
print("Created credentials object:", creds)

from google.cloud import firestore
db = firestore.Client(project="project-df7e2989-3b91-42b5-9e1", credentials=creds)
print("Connected to Firestore client:", db)
try:
    cols = list(db.collections())
    print("Firestore collections retrieved successfully:", [c.id for c in cols])
except Exception as e:
    print("Firestore query error:", e)
