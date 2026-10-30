# cupl.ai — The Relational AI Concierge for Modern Couples 💍✨

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.3-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash_%26_Pro-4285F4?logo=google&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Qloo Cultural AI](https://img.shields.io/badge/Qloo-Cultural_Taste_Graph-FF4081)](https://qloo.com)
[![Google Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Serverless-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

> **"India is the 2nd largest wedding market in the world, hosting approximately 1 in every 4 weddings globally. Couples and families spend lakhs—often life savings—on celebrations alone. Yet, there is a glaring absence of large-scale, tech-driven brands solving this space."**  
> — *[Zerodha Founder Probes India’s Wedding Brand Gap in 2nd Largest Market](https://startuppedia.in/trending/zerodha-founder-probes-india-wedding-brand-gap-in-2nd-largest-market-4529391)*

**cupl.ai** is the world's first **Relational AI Concierge** engineered for multicultural couples. Unlike conventional single-user assistants or legacy wedding tools that get uninstalled immediately after the wedding day (the fatal **"Churn Cliff"**), cupl.ai fuses **Qloo's Cultural Taste Graph** with **Google Gemini 2.5** to mathematically intersect two partners' cultural traditions, dining aesthetics, musical tastes, and lifestyle preferences—powering milestone celebrations and everyday life together.

---

## 🌟 Core Innovations

### 1. 👑 Milestone Masterplans with Practical Engineering
Dynamic, executable masterplans across 5 core spaces:
* **Weddings:** Dual-heritage itineraries, guest scale capacity buffers, and anti-clash attire palettes.
* **Pre-Weddings & Engagements:** Authentic ceremony sequencing (e.g., Vedic rituals harmonized with Telugu Pellikuthuru).
* **3-Phase Sangeet Energy Curves:** Real tempo transition curves (95 BPM acoustic folk warm-up $\rightarrow$ 114 BPM retro fusion $\rightarrow$ 128 BPM peak Bollywood dhol).
* **Anti-Waste Catering Portions:** Headcount-based catering algorithms saving $\approx$ ₹75,000 in surplus food per celebration.
* **Honeymoons & Couple Trips:** Day-by-day travel routes scored against joint couple affinities.

### 2. 📋 Collaborative Shared Blueprints
Shared living plans co-created through natural conversation with cupl AI (e.g., Weekend Getaways, Choreography, First Living Room Revamp). Features real-time status tracking (**Loved**, **Skipped**, **Confirmed**) and filter chips.

### 3. ✨ Continuous Recommends Across 8 Lifestyle Pillars
Continuous taste affinity updates spanning **Dining, Music, Fashion, Travel, Film, Nightlife, Books, and Podcasts**. Delivers hyper-personalized joint discovery (e.g., *"There is a new movie release with a 95% match with your shared couple taste"*).

### 4. 🔒 The Couple Gatekeeper (Relational AI Guardrail)
The first agentic guardrail designed specifically for couples. cupl AI refuses to generate a one-sided plan when one partner tries to plan in isolation:
> *"Awaiting Bride's Tastes & Aesthetic ✨ Narayan, to weave an authentic dual-heritage masterplan, Amruta needs to be onboarded so her traditions and music are harmonized with yours."*

### 5. 🎁 Intelligent Surprise Engine (Zero-Leak Private Vault)
Allows one partner to plan secret dates, anniversary trips, or birthday gifts using their partner's taste graph. Kept in a cryptographically isolated vault with zero leaks into the shared couple feed.

### 6. 🎙️ Multimodal AI Companion Stage
An interactive conversation studio featuring live streaming text captions, animated audio-reactive companion pulses powered by the Web Audio API, and native low-latency audio interaction.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────┐
│               React 18 + Vite Web App                  │
│       TailwindCSS • Lucide Icons • Web Audio API       │
└──────────────────────────┬─────────────────────────────┘
                           │ REST / SSE / WebSocket
┌──────────────────────────▼─────────────────────────────┐
│                   FastAPI Backend                      │
│       Session Management • Firestore DB • Cloud Run    │
└────────────┬─────────────────────┬─────────────────────┘
             │                     │                     │
┌────────────▼─────┐ ┌─────────────▼───────┐ ┌───────────▼───────┐
│  Google Vertex   │ │      cupl MCP       │ │   Qloo Cultural   │
│    Gemini 2.5    │◄┼──►    Server        │◄┼─►   Taste API     │
│  (Tool Caller)   │ │      (36 Tools)     │ │  (Taste Graph)    │
└──────────────────┘ └─────────────────────┘ └───────────────────┘
```

---

## ⚙️ The cupl MCP Server (36 Specialized Tools)

Rather than relying on brittle prompt engineering, cupl AI uses a dedicated **Model Context Protocol (MCP)** server providing **36 deterministic tools** to Google Gemini:

| Domain | Capability / Tools |
|---|---|
| **Cultural Taste & Qloo** | `search_entities`, `get_cultural_affinities`, `resolve_tastes`, `compute_joint_overlap` |
| **Milestone Spaces** | `create_space`, `get_space_masterplan`, `update_space_section`, `calculate_guest_math` |
| **Collaborative Plans** | `create_plan`, `update_plan_status`, `add_agenda_item`, `set_action_items` |
| **Couple Gatekeeper** | `check_partner_onboarding_status`, `enforce_dual_perspective_guardrail` |
| **Surprise Vault** | `create_private_surprise`, `fetch_partner_secret_interests`, `lock_surprise_vault` |
| **Episodic Memory** | `store_interaction_memory`, `query_vector_context`, `update_taste_dna` |

---

## 💻 Technology Stack

| Layer | Technology |
|---|---|
| **AI Reasoning & LLM** | Google Gemini 2.5 Pro & 2.5 Flash via Google Cloud Vertex AI |
| **Cultural Intelligence** | Qloo Cultural AI API (Entities, Cross-Domain Affinities, Tastes) |
| **Agent Protocol** | cupl Model Context Protocol (MCP) Server (Streamable HTTP, 36 Tools) |
| **Backend Framework** | FastAPI (Python 3.12, Uvicorn, AsyncIO, Pydantic v2) |
| **Database & Vector Memory** | Google Cloud Firestore (Native mode, Subcollections, Vector Search) |
| **Frontend Framework** | React 18, TypeScript, Vite, React Router v6 |
| **Styling & Icons** | TailwindCSS, Lucide React, Glassmorphic Design System |
| **Audio & Multimodal** | Web Audio API, AudioContext, Canvas Real-Time Visualizer |
| **Cloud Infrastructure** | Google Cloud Run (Containerized, Auto-scaling, HTTP/2, WebSockets) |

---

## 📂 Project Structure

```text
cupl.ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint
│   │   ├── config.py            # Pydantic environment configuration
│   │   ├── auth.py              # Dual-partner session & auth handlers
│   │   ├── db.py                # Firestore client & transaction helpers
│   │   ├── routes/              # REST & SSE API endpoints (chat, spaces, me, plans)
│   │   ├── services/            # Taste intersection, gatekeeper, space services
│   │   └── toolkit/             # cupl MCP server (36 tools & registry)
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Production multi-stage container
├── frontend/
│   ├── src/
│   │   ├── pages/               # ChatPage, SpaceView, MePage, RecommendsPage, OurPlans
│   │   ├── components/          # CompanionStage, PlanDetailModal, SurpriseModal
│   │   ├── api/                 # Typed client API & SSE streaming consumers
│   │   └── index.css            # Tailwind typography & bespoke theme tokens
│   ├── package.json             # NPM package manifest
│   └── vite.config.ts           # Vite bundler configuration
├── infra/                       # Cloud Run deployment & Firestore security rules
└── scripts/                     # Verified couple seeding & profile utilities
```

---

## 🚀 Quickstart

### Prerequisites
* **Python 3.12+**
* **Node.js 18+** & **npm 9+**
* **Google Cloud Project** with Vertex AI & Firestore enabled
* **Qloo API Key**

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in your GCP_PROJECT, VERTEX_LOCATION, and QLOO_API_KEY
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Production Couple Seeding (Optional)
To load the authentic dual-heritage demo couple (Narayan & Amruta):
```bash
python scripts/seed_full_production_couple.py
python scripts/seed_tastes_facts.py
```

---

## ☁️ Deployment

Deploy backend and frontend bundle directly to **Google Cloud Run**:

```bash
# Build frontend
cd frontend
npm run build
cp -r dist ../backend/dist

# Deploy to Cloud Run
cd ../backend
gcloud run deploy cupl-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=live,GCP_PROJECT=YOUR_PROJECT_ID \
  --set-secrets QLOO_API_KEY=qloo-key:latest
```

---

## 👥 Authors & Acknowledgments

* **Narayan Ajanikar** ([@ajnikareer](https://github.com/ajnikareer))
* Built for the **Qloo AI Hackathon** powered by **Google Cloud Vertex AI & Qloo**.

---

## 📄 License

This project is licensed under the Apache 2.0 License.

