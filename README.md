# WeaveWed v2 — happily ever after 💞

A voice + chat **agentic AI** companion that plans every chapter of a couple's love story — prewedding, engagement,
wedding (ceremony by ceremony), honeymoon, trips and life beyond — powered by **Gemini** (Vertex AI, Live native audio)
and **QLOO** taste intelligence, with every product capability served by the **WeaveWed MCP server**.

**Live product. No demo or seed data.** If QLOO or Gemini fails you see a real, friendly error — never filler.

```
weavewed/
├─ backend/                 FastAPI app = REST API + WeaveWed MCP server (/mcp/) + voice WebSocket (/ws/voice)
│  ├─ app/toolkit/          32 product tools (single source of truth) — published over MCP
│  ├─ app/mcp_server.py     MCP Streamable HTTP server
│  ├─ app/agent/            text agent, voice agent, layered prompts + skills, MCP tool client
│  ├─ app/services/         taste intelligence, QLOO client, plan engine, Director, memory, learning, DNA …
│  ├─ scripts/check_live.py live smoke test against real QLOO + Gemini
│  └─ tests/offline/        102-check offline suite (real MCP server+client, fake cloud)
├─ frontend/                React + Vite + Tailwind — one responsive app for web & mobile (installable PWA)
├─ infra/                   GCP setup, Cloud Run deploy, Firestore rules & vector index, Firebase hosting
└─ AGENT_HANDOFF.md         read this first if you're an AI coding agent
```

## 1. Prerequisites
- GCP project with billing + `gcloud` CLI; Firebase project on the **same** GCP project
- Python 3.12, Node 20+, a QLOO API key + its base URL

## 2. One-time setup
```bash
PROJECT=your-project REGION=asia-south1 bash infra/setup_gcp.sh
```
**Firebase console:** Authentication → enable **Google** + **Email/Password**; Settings → Authorized domains → add
`localhost` and your hosting domain; Project settings → add a **Web app** → copy config into `frontend/.env`.

**Models:** confirm in Vertex AI Model Garden the current names for the Live native-audio model, Flash, Pro and
embeddings; set them in `backend/.env`. `VERTEX_LOCATION` must be a region where the Live model is available.

## 3. Run locally
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # GCP_PROJECT, QLOO_API_KEY, MCP_INTERNAL_TOKEN (any 32+ random chars), models
gcloud auth application-default login
python -m scripts.check_live                              # ✅ verify QLOO + taste intelligence + Gemini + Live voice
uvicorn app.main:app --port 8080
curl "http://localhost:8080/healthz?deep=true"            # firestore, qloo, gemini, mcp, taste_intel

# frontend (new terminal)
cd frontend && npm install && cp .env.example .env && npm run dev     # http://localhost:5173
```
Voice needs mic permission (works on localhost and HTTPS). Use headphones on laptops for the cleanest barge-in.

## 4. Deploy
```bash
PROJECT=your-project REGION=asia-south1 WEB_ORIGIN=https://your-project.web.app QLOO_BASE_URL=<your qloo url> bash infra/deploy_api.sh
cd frontend && echo "VITE_API_BASE=<Cloud Run URL>" >> .env && npm run build && cd ..
npm i -g firebase-tools && firebase login
firebase deploy --config infra/firebase.json --project your-project --only hosting,firestore
```

## 5. Use the MCP server from other clients (e.g. VS Code)
`https://<cloud-run-url>/mcp/` — Streamable HTTP. Header `Authorization: Bearer <Firebase ID token of a user>`.
All 32 tools run as that user with the same rules as the in-app agent (event gate, privacy, validation).

## 6. Manual live test (two real accounts)
1. Sign up as A, open chat: agent welcomes you, asks ONE light question (no interrogation).
2. "We're getting married in Udaipur next February" → event created; it asks the next missing detail one at a time.
3. Say "I love Arijit Singh and hate loud DJs" → Me page shows **Arijit Singh** (music, matched) and **✗ loud DJ music**.
4. Say "I like Mercury" (ambiguous) → a "Which one did you mean?" card appears.
5. Agent asks your music/film/fashion taste → picker with live chips; search + add your own. Max 2 taste questions in a row.
6. Invite B (Me page or ask the agent) → B joins, lands in the same event; picks tastes; 💞 marks A's picks.
7. "Build our plan" → agent keeps chatting while sections appear live on the event page; "Why this?", Maps, ♥/✕/✓.
8. "No loud DJs, more Sufi for the Sangeet" → only the Sangeet section rebuilds.
9. Tap **Talk**: voice screen with avatar + waveform; interrupt it mid-sentence; tap chips while talking;
   ask it to build/revise the plan — when ready it tells you at the next natural pause.
10. Trip with no destination → destinations suggested → places/food/itinerary for the top match.
11. Memories tab: "loved the quiet sunset dinner, hated crowds" → a later trip plan recalls it.
12. "Plan a surprise for Karan's birthday" → only A sees it (Surprises page); B's agent never mentions it.

## 7. Honest limits
Recommends & links to Maps — no booking. Costs are estimates. QLOO venue coverage varies by city: sections with no
matches say so (nothing invented). Notifications are in-app (web push not in v2).
