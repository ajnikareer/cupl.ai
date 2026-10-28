# Offline test suite (no cloud needed)
Runs the REAL FastAPI app + REAL WeaveWed MCP server (Streamable HTTP) + REAL MCP client, with an in-memory Firestore,
fake QLOO responses and scripted Gemini. Use it after every code change.

    cd backend
    pip install -r requirements.txt websockets
    python tests/offline/run_all.py

| Suite | Covers |
|---|---|
| test_mcp_tools.py | MCP transport + auth, 32 tools, mode gate, taste intelligence (Arijit→music→exact entity, Sufi→tag, ambiguity card), picker save, partner join, DNA, background plan builds, candidate-only guardrail, QLOO signals, privacy |
| test_e2e_agent.py | text agent loop: streaming, tool calls through MCP, context refresh after mutations, widgets, picker answers, Director stages, LLM failure, learning worker |
| test_e2e_api.py | every REST endpoint, SSE chat, budget, todos, memories, cron check-ins, self-healing state, deep health, partner join |
| test_e2e_voice.py | voice proxy: feature auto-fallback, tool calls, audio both ways, transcripts, plan-ready injection, go_away resume, clean hang-up |
