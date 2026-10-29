import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core import llm
from app.config import settings
from google.genai import types

async def test_live_tool():
    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="get_time",
            description="Returns current time",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        )
    ])]
    cfg = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        tools=tools,
        system_instruction=types.Content(parts=[types.Part(text="You are a voice assistant. When asked for time, call get_time and then speak the time.")]),
    )
    async with llm.client.aio.live.connect(model=settings.GEMINI_LIVE_MODEL, config=cfg) as s:
        print("Connected to live Gemini Live session.")
        await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text="What time is it?")]), turn_complete=True)
        print("Sent prompt: What time is it?")
        
        async for resp in s.receive():
            if resp.tool_call:
                print("Received tool call:", resp.tool_call)
                fc = resp.tool_call.function_calls[0]
                resp_payload = [types.FunctionResponse(id=fc.id, name=fc.name, response={"result": {"time": "7:45 PM"}})]
                print("Sending tool response:", resp_payload)
                await s.send_tool_response(function_responses=resp_payload)
                print("Tool response sent! Waiting for model response...")
            if resp.server_content:
                sc = resp.server_content
                if sc.model_turn:
                    for p in sc.model_turn.parts or []:
                        if p.inline_data:
                            print(f"Received audio bytes: {len(p.inline_data.data)}")
                if sc.output_transcription:
                    print("Transcript:", sc.output_transcription.text)
                if sc.turn_complete:
                    print("Turn complete!")
                    break

if __name__ == "__main__":
    asyncio.run(test_live_tool())
