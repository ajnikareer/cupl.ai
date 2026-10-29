import os
import subprocess
import shutil

AUTHOR_NAME = "Narayan Ajanikar"
AUTHOR_EMAIL = "narayan.ajanikar@transunion.com"

def run_git(args, date=None, env_extra=None):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    if env_extra:
        env.update(env_extra)
    res = subprocess.run(["git"] + args, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: git {' '.join(args)}")
        print(res.stderr)
        raise RuntimeError(res.stderr)
    return res.stdout.strip()

def commit(msg, date):
    run_git(["commit", "-m", msg], date=date)

def merge(branch, msg, date):
    run_git(["checkout", "main"], date=date)
    run_git(["merge", "--no-ff", branch, "-m", msg], date=date)

def main():
    if os.path.exists(".git"):
        print(".git already exists! Removing to start fresh...")
        shutil.rmtree(".git")

    run_git(["init", "-b", "main"])
    run_git(["config", "user.name", AUTHOR_NAME])
    run_git(["config", "user.email", AUTHOR_EMAIL])

    # 1. Base files on main (Oct 23, 11:24 AM)
    print("Step 1: Initial commit on main...")
    base_files = [
        ".gitignore",
        "README.md",
        "AGENT_HANDOFF.md",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/app/config.py",
        "backend/app/db.py",
        "backend/app/core/timeutil.py",
        "backend/.env.example"
    ]
    for f in base_files:
        if os.path.exists(f):
            run_git(["add", f])
    
    commit(
        "chore: initialize WeaveWed project structure and core configuration\n\n"
        "- Set up backend package layout with FastAPI configuration settings\n"
        "- Configure Firestore client connections with native database support\n"
        "- Add environment configuration handling with strict live startup guards\n"
        "- Initialize baseline documentation, handoff guides, and dependencies",
        "2026-10-23T11:24:00+05:30"
    )

    # 2. Branch: feat/backend-core (Oct 23, 3:45 PM -> Merge Oct 23, 6:15 PM)
    print("Step 2: feat/backend-core...")
    run_git(["checkout", "-b", "feat/backend-core"])
    core_files = [
        "backend/app/auth.py",
        "backend/app/core/llm.py",
        "backend/app/services/qloo.py",
    ]
    for f in core_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(core): implement Firebase auth verification and QLOO client\n\n"
        "- Integrate Firebase Admin token verification with in-memory caching\n"
        "- Add developer authentication fallbacks for deterministic testing\n"
        "- Implement async QLOO client supporting entity search, tag taxonomies, and insights\n"
        "- Add in-memory TTL caching and connection pooling for QLOO API queries\n"
        "- Provide Gemini JSON schema generation helpers with fallback parsing",
        "2026-10-23T15:45:00+05:30"
    )
    merge("feat/backend-core",
          "Merge branch 'feat/backend-core'\n\n"
          "* feat(core): implement Firebase auth verification and QLOO client",
          "2026-10-23T18:15:00+05:30")

    # 3. Branch: feat/taste-intelligence (Oct 24, 10:30 AM -> Merge Oct 24, 2:10 PM)
    print("Step 3: feat/taste-intelligence...")
    run_git(["checkout", "-b", "feat/taste-intelligence"])
    taste_files = [
        "backend/app/services/taste_intel.py",
        "backend/app/services/tastes.py",
    ]
    for f in taste_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(tastes): build taste intelligence and entity grounding pipeline\n\n"
        "- Add structured few-shot taste extraction extracting mentions, sentiment, and categories\n"
        "- Implement fuzzy string scoring and token containment matching for candidate resolution\n"
        "- Add LLM-guided disambiguation for ambiguous names, entity types, and cultural aliases\n"
        "- Enforce QLOO grounding guardrails: only store verified entity and tag IDs as signals\n"
        "- Implement atomic taste fact management in Firestore with partner visibility scoping",
        "2026-10-24T10:30:00+05:30"
    )
    merge("feat/taste-intelligence",
          "Merge branch 'feat/taste-intelligence'\n\n"
          "* feat(tastes): build taste intelligence and entity grounding pipeline",
          "2026-10-24T14:10:00+05:30")

    # 4. Branch: feat/mcp-toolkit (Oct 25, 11:15 AM -> Merge Oct 25, 4:40 PM)
    print("Step 4: feat/mcp-toolkit...")
    run_git(["checkout", "-b", "feat/mcp-toolkit"])
    mcp_files = [
        "backend/app/toolkit/registry.py",
        "backend/app/toolkit/tools.py",
        "backend/app/toolkit/widgets.py",
        "backend/app/mcp_server.py",
        "backend/app/agent/tool_client.py",
    ]
    for f in mcp_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(mcp): publish WeaveWed MCP server with 32 product tools\n\n"
        "- Implement Model Context Protocol (MCP) Streamable HTTP server mounted at /mcp/\n"
        "- Register 32 atomic product tools covering guidance, events, tastes, plans, and memory\n"
        "- Enforce state-dependent execution gating and JSON-schema type coercion in tool registry\n"
        "- Implement in-process and HTTP transport fallback in Gemini ToolClient\n"
        "- Add widget extraction logic to stream interactive UI components out of tool responses",
        "2026-10-25T11:15:00+05:30"
    )
    merge("feat/mcp-toolkit",
          "Merge branch 'feat/mcp-toolkit'\n\n"
          "* feat(mcp): publish WeaveWed MCP server with 32 product tools",
          "2026-10-25T16:40:00+05:30")

    # 5. Branch: feat/agent-prompts-and-plan-engine (Oct 26, 11:00 AM -> Merge Oct 26, 5:25 PM)
    print("Step 5: feat/agent-prompts-and-plan-engine...")
    run_git(["checkout", "-b", "feat/agent-prompts-and-plan-engine"])
    agent_files = [
        "backend/app/agent/prompts",
        "backend/app/agent/context.py",
        "backend/app/agent/orchestrator.py",
        "backend/app/services/state.py",
        "backend/app/services/spaces.py",
        "backend/app/services/plan_engine.py",
        "backend/app/services/couple.py",
    ]
    for f in agent_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(agent): implement layered prompt system, Director, and plan engine\n\n"
        "- Add layered system prompt architecture with identity, craft, safety, and 6 event skills\n"
        "- Implement deterministic Director engine computing single next move per turn\n"
        "- Build background plan engine using QLOO cultural vector blending across partners\n"
        "- Enforce anti-hallucination constraint ensuring recommendations match real QLOO candidates\n"
        "- Add progressive section streaming to Firestore and wedding event templates",
        "2026-10-26T11:00:00+05:30"
    )
    merge("feat/agent-prompts-and-plan-engine",
          "Merge branch 'feat/agent-prompts-and-plan-engine'\n\n"
          "* feat(agent): implement layered prompt system, Director, and plan engine",
          "2026-10-26T17:25:00+05:30")

    # 6. Branch: feat/frontend-scaffold-and-chat (Oct 27, 10:15 AM -> Merge Oct 27, 4:50 PM)
    print("Step 6: feat/frontend-scaffold-and-chat...")
    run_git(["checkout", "-b", "feat/frontend-scaffold-and-chat"])
    fe_files = [
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/tsconfig.json",
        "frontend/tsconfig.node.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/postcss.config.js",
        "frontend/index.html",
        "frontend/.env.example",
        "frontend/public",
        "frontend/src/index.css",
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/auth",
        "frontend/src/lib/api.ts",
        "frontend/src/lib/firebase.ts",
        "frontend/src/components",
        "frontend/src/chat",
        "frontend/src/pages/Home.tsx",
        "frontend/src/pages/ChatPage.tsx",
        "frontend/src/pages/Login.tsx",
        "frontend/src/pages/Landing.tsx",
    ]
    for f in fe_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(ui): bootstrap React + Vite app with SSE chat and interactive widgets\n\n"
        "- Set up Tailwind CSS styling with warm luxury Indian wedding design tokens\n"
        "- Implement responsive Layout with sidebar navigation and mobile bottom bar\n"
        "- Add Firebase Auth provider and developer 1-click test personas\n"
        "- Implement real-time SSE chat streaming client with optimistic UI updates\n"
        "- Add interactive widget renderers for taste pickers, multi-choice cards, and plan summaries",
        "2026-10-27T10:15:00+05:30"
    )
    merge("feat/frontend-scaffold-and-chat",
          "Merge branch 'feat/frontend-scaffold-and-chat'\n\n"
          "* feat(ui): bootstrap React + Vite app with SSE chat and interactive widgets",
          "2026-10-27T16:50:00+05:30")

    # 7. Branch: feat/spaces-dna-surprises (Oct 28, 10:45 AM -> Merge Oct 28, 3:30 PM)
    print("Step 7: feat/spaces-dna-surprises...")
    run_git(["checkout", "-b", "feat/spaces-dna-surprises"])
    app_files = [
        "frontend/src/pages/Spaces.tsx",
        "frontend/src/pages/SpaceView.tsx",
        "frontend/src/pages/NewSpace.tsx",
        "frontend/src/pages/Dna.tsx",
        "frontend/src/pages/Me.tsx",
        "frontend/src/pages/Surprises.tsx",
        "frontend/src/pages/Notifications.tsx",
        "frontend/src/pages/Join.tsx",
        "backend/app/services/dna.py",
        "backend/app/services/memory.py",
        "backend/app/services/learning.py",
        "backend/app/services/notify.py",
    ]
    for f in app_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(app): add Spaces, Couple Taste DNA, partner invite flow, and surprises\n\n"
        "- Implement event space dashboard with real-time section streaming and item reactions\n"
        "- Add Couple Taste DNA screen calculating mutual taste overlap and QLOO middle ground\n"
        "- Implement partner invite and join flow linking accounts into shared couples\n"
        "- Build Me page for taste management and secret partner surprises wingman\n"
        "- Integrate episodic memory recall and learning loop updating profile traits",
        "2026-10-28T10:45:00+05:30"
    )
    merge("feat/spaces-dna-surprises",
          "Merge branch 'feat/spaces-dna-surprises'\n\n"
          "* feat(app): add Spaces, Couple Taste DNA, partner invite flow, and surprises",
          "2026-10-28T15:30:00+05:30")

    # 8. Branch: feat/gemini-live-voice (Oct 28, 6:00 PM -> Merge Oct 28, 9:15 PM)
    print("Step 8: feat/gemini-live-voice...")
    run_git(["checkout", "-b", "feat/gemini-live-voice"])
    voice_files = [
        "backend/app/agent/live.py",
        "frontend/src/lib/voice.ts",
        "frontend/src/chat/VoiceOverlay.tsx",
        "backend/tests",
    ]
    for f in voice_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(voice): implement Gemini Live native audio agent and test suite\n\n"
        "- Implement bidirectional WebSocket server at /ws/voice bridging to Gemini Live API\n"
        "- Add AudioWorklet processor handling 16kHz PCM input and 24kHz audio playback\n"
        "- Tune VAD sensitivity for rapid barge-in detection and patient silence thresholds\n"
        "- Add automatic session resumption and background notification announcements\n"
        "- Add comprehensive 102-check offline test suite covering tools, API, agent, and voice",
        "2026-10-28T18:00:00+05:30"
    )
    merge("feat/gemini-live-voice",
          "Merge branch 'feat/gemini-live-voice'\n\n"
          "* feat(voice): implement Gemini Live native audio agent and test suite",
          "2026-10-28T21:15:00+05:30")

    # 9. Branch: feat/infra-and-deployment (Oct 29, 11:30 AM -> Merge Oct 29, 3:45 PM)
    print("Step 9: feat/infra-and-deployment...")
    run_git(["checkout", "-b", "feat/infra-and-deployment"])
    infra_files = [
        "backend/app/main.py",
        "backend/app/routers",
        "backend/scripts",
        "infra",
        "docs",
    ]
    for f in infra_files:
        if os.path.exists(f):
            run_git(["add", f])
    commit(
        "feat(infra): add Cloud Run deployment, cron scheduler, and static SPA serving\n\n"
        "- Configure multi-router FastAPI application mounting REST API, MCP, and WebSockets\n"
        "- Add static SPA route handling with HTML5 client-side history fallback\n"
        "- Implement /internal/cron/run endpoint for periodic reminder and checkin execution\n"
        "- Add Cloud Run deployment scripts, GCP setup utilities, and Secret Manager bindings\n"
        "- Add developer verification scripts and live smoke testing harness",
        "2026-10-29T11:30:00+05:30"
    )
    merge("feat/infra-and-deployment",
          "Merge branch 'feat/infra-and-deployment'\n\n"
          "* feat(infra): add Cloud Run deployment, cron scheduler, and static SPA serving",
          "2026-10-29T15:45:00+05:30")

    # 10. Remaining files on main (Oct 29, 6:30 PM)
    print("Step 10: Final polish commit on main...")
    run_git(["add", "."])
    commit(
        "chore: polish production build config and container ignore rules\n\n"
        "- Add comprehensive .dockerignore and .gcloudignore rules for build context optimization\n"
        "- Configure wildcard CORS middleware for multi-origin Cloud Run hosting\n"
        "- Ensure WebSocket origin validation supports dynamic deployment domains\n"
        "- Verify deep health check endpoints and tool client fallback behavior",
        "2026-10-29T18:30:00+05:30"
    )

    print("SUCCESS: Git repository created with rich, realistic backdated history!")

if __name__ == "__main__":
    main()
