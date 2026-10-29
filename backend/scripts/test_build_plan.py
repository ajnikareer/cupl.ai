import urllib.request
import json
import time

headers = {
    "Authorization": "Bearer dev-narayan",
    "Content-Type": "application/json"
}

# 1. Get spaces
req = urllib.request.Request("http://127.0.0.1:8080/api/spaces", headers={"Authorization": "Bearer dev-narayan"})
with urllib.request.urlopen(req) as resp:
    sp = json.loads(resp.read().decode())
    space_id = sp["spaces"][0]["id"]
    print("Target Space ID:", space_id)

# 2. Add ceremonies
patch_data = json.dumps({"fields": {"ceremonies": ["Mehendi", "Sangeet", "Wedding", "Reception"]}}).encode()
req2 = urllib.request.Request(f"http://127.0.0.1:8080/api/spaces/{space_id}", data=patch_data, headers=headers, method="PATCH")
with urllib.request.urlopen(req2) as resp:
    print("PATCH result:", json.loads(resp.read().decode()))

# 3. Add a few tastes for Narayan
tastes = [
    {"text": "Arijit Singh", "category": "music", "sentiment": 1},
    {"text": "Amit Trivedi", "category": "music", "sentiment": 1},
    {"text": "Sabyasachi Mukherjee", "category": "fashion", "sentiment": 1},
    {"text": "The Leela Palace Udaipur", "category": "place", "sentiment": 1},
    {"text": "Rajasthani Dal Baati Churma", "category": "food", "sentiment": 1}
]
for t in tastes:
    data = json.dumps(t).encode()
    r = urllib.request.Request("http://127.0.0.1:8080/api/tastes", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r) as resp:
            print("Added taste:", t["text"])
    except Exception as e:
        print("Taste error:", t["text"], e)

# 4. Trigger build plan
build_req = urllib.request.Request(f"http://127.0.0.1:8080/api/spaces/{space_id}/plan", data=json.dumps({}).encode(), headers=headers, method="POST")
with urllib.request.urlopen(build_req) as resp:
    print("Build plan triggered:", json.loads(resp.read().decode()))

# 5. Poll plan until complete
print("Waiting for plan synthesis (Gemini 2.5 Flash + Qloo Grounding)...")
for i in range(25):
    time.sleep(2)
    check_req = urllib.request.Request(f"http://127.0.0.1:8080/api/spaces/{space_id}", headers={"Authorization": "Bearer dev-narayan"})
    with urllib.request.urlopen(check_req) as resp:
        space_info = json.loads(resp.read().decode())
        state = space_info.get("state")
        print(f"[{i*2}s] Space state: {state}")
        if state == "ready":
            break

# 6. Fetch final plan
plan_req = urllib.request.Request(f"http://127.0.0.1:8080/api/spaces/{space_id}/plan", headers={"Authorization": "Bearer dev-narayan"})
with urllib.request.urlopen(plan_req) as resp:
    plan = json.loads(resp.read().decode())
    print("PLAN SECTIONS:", len(plan.get("sections", [])))
    for s in plan.get("sections", []):
        print(f"  * {s.get('title')} ({len(s.get('items', []))} items)")
        for item in s.get("items", [])[:2]:
            print(f"      - {item.get('title')} | {item.get('affinity')} | Why: {item.get('why')[:1]}")

