import os

# 1. Update backend/app/toolkit/tools.py
with open('backend/app/toolkit/tools.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'from ..services import couple as couple_svc\nfrom ..services import dna as dna_svc',
    'from ..services import calendar_svc, couple as couple_svc, dna as dna_svc, recommends_svc'
)

new_tools = '''

# ============================== Everyday Couple Plans & Recommendations ==============================
@tool("add_couple_plan", "plans", """Add an everyday couple plan to the couple's Plans tab and unified Calendar (e.g. movie streaming night, romantic dinner, spontaneous 2-day getaway, or couple experience).
Takes: title, category (movie, dining, travel, cocktail, decor, music, experience), date (YYYY-MM-DD), time (e.g. '8:00 PM'), description, maps_url (optional), is_private (optional).
Call this whenever the couple agrees on an everyday date, movie night, dinner reservation, or getaway to schedule.""",
      obj({"title": S, "category": {"type": "string", "enum": ["movie", "dining", "travel", "cocktail", "decor", "music", "experience"]},
           "date": DATE, "time": S, "description": S, "maps_url": S, "is_private": B}, ["title", "category", "date"]), mutates=True)
async def add_couple_plan(c, a):
    item = await calendar_svc.add_calendar_item(c.user, {
        "title": a["title"],
        "category": a.get("category", "dining"),
        "date": a["date"],
        "time": a.get("time"),
        "description": a.get("description", ""),
        "maps_url": a.get("maps_url"),
        "is_private": a.get("is_private", False),
    })
    return {
        "ok": True,
        "plan_id": item.get("id"),
        "title": a["title"],
        "date": a["date"],
        "message": f"Added '{a['title']}' to your couple Plans and Calendar for {a['date']} ✨"
    }


@tool("get_lifestyle_recommends", "recommends", """Fetch the couple's active curated lifestyle recommendations (Friday night movies, weekend dining, signature cocktails, living room decor, spontaneous getaways) tailored to their Couple Taste DNA and life-stage.
Call this when the user asks for recommendations, date night ideas, movie suggestions, or weekend escapes.""",
      obj({}, []))
async def get_lifestyle_recommends(c, a):
    recs = await recommends_svc.get_lifestyle_recommendations(c.user)
    return {
        "couple_vibe": recs.get("couple_vibe"),
        "active_city": recs.get("active_city"),
        "couple_status": recs.get("couple_status"),
        "recommendations": [
            {
                "id": r["id"],
                "category": r["category"],
                "category_label": r.get("category_label"),
                "title": r["title"],
                "subtitle": r.get("subtitle"),
                "affinity": r.get("affinity"),
                "description": r.get("description"),
                "why": r.get("why"),
                "suggested_date": r.get("suggested_date"),
                "est_cost": r.get("est_cost"),
                "maps_url": r.get("maps_url"),
            }
            for r in recs.get("couple_recs", [])[:4]
        ]
    }
'''

if 'def add_couple_plan' not in text:
    text += new_tools

with open('backend/app/toolkit/tools.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated backend/app/toolkit/tools.py successfully!')

# 2. Update backend/app/services/state.py
with open('backend/app/services/state.py', 'r', encoding='utf-8') as f:
    st_text = f.read()

old_welcome = '''    # 2. Initial Welcome for solo user
    if turns < 2 and not prof.get("greeted"):
        nxt.update(stage="welcome", goal=f"Warmly welcome {first}. Introduce yourself in one line and ask, lightly, what "
                   "they're celebrating or planning right now. Do NOT ask for dates, budget or tastes yet.")
        return nxt'''

new_welcome = '''    # 2. Initial Welcome for solo user (Exact cupl AI Tour protocol)
    if turns < 2 and not prof.get("greeted"):
        nxt.update(stage="welcome", goal=f"Warmly welcome {first}: 'Hello {first}! Welcome to cupl AI — your AI concierge for life together. "
                   "How can I help you today? Would you like a quick tour of what ways I can assist you, or is there an upcoming celebration or weekend plan on your mind?' "
                   "Do NOT ask for dates, budget or tastes yet.")
        return nxt'''

st_text = st_text.replace(old_welcome, new_welcome)

with open('backend/app/services/state.py', 'w', encoding='utf-8') as f:
    f.write(st_text)

print('Updated backend/app/services/state.py successfully!')

# 3. Update backend/app/agent/prompts/tools_playbook.md
with open('backend/app/agent/prompts/tools_playbook.md', 'r', encoding='utf-8') as f:
    pb_text = f.read()

new_playbook_section = '''
- **Everyday Couple Plans:** Whenever the user wants to plan a date night, dinner reservation, movie streaming night, or spontaneous getaway, call **add_couple_plan**. This immediately saves the plan to their **Plans** tab and unified **Calendar** with clean category badges and maps links.
- **Weekly Lifestyle Recommendations:** Call **get_lifestyle_recommends** whenever the couple asks for date night inspiration, weekend activities, or movie picks. These are 100% grounded in their Couple Taste DNA and life-stage.
- **Onboarding Tour Script:** When a user asks what cupl AI does or accepts the tour, walk them through the 4 core pillars:
  1. *Powered by QLOO Cultural Taste Intelligence:* Mapping both your tastes across music, cinema, cuisine, fashion, and travel to uncover where your worlds harmonize.
  2. *Milestone Events:* Royal Weddings, Engagements, Preweddings, Honeymoons, Trips, Anniversaries with dual-heritage rituals, anti-waste portioning math, and multi-generational music curves.
  3. *Everyday Couple Plans:* Friday movie streaming stand-offs, weekend dinner tables, and spontaneous getaways — planned right here in chat and added directly to your Plans tab.
  4. *Weekly Recommendations & Reminders:* 4 fresh weekly lifestyle picks, reminders, and calendar conflict avoidance.
- **Taste-First Collection Principle:** Before creating plans or recommendations, ensure core tastes are collected via **remember_tastes** and **show_taste_picker**.
- **Couple Gatekeeper:** Never weave a couple event masterplan with only one partner's tastes without offering **invite_partner** first.
'''

if 'Everyday Couple Plans:' not in pb_text:
    pb_text += new_playbook_section

with open('backend/app/agent/prompts/tools_playbook.md', 'w', encoding='utf-8') as f:
    f.write(pb_text)

print('Updated backend/app/agent/prompts/tools_playbook.md successfully!')

