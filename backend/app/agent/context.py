"""Assembles the layered system prompt from prompt files + one live Snapshot."""
from pathlib import Path

from ..core.timeutil import local_now
from ..services import spaces as sp
from ..services.state import Snapshot
from ..services.tastes import coverage

P = Path(__file__).parent / "prompts"
_read = lambda n: (P / n).read_text(encoding="utf-8")  # noqa: E731
BASE = "\n\n".join(_read(n) for n in ["identity.md", "conversation.md", "tools_playbook.md", "privacy.md", "examples.md"])
VOICE = _read("voice.md")
SKILLS = {t: _read(f"skills/{t}.md") for t in sp.TEMPLATES}

MODE_RULES = {
    "guide": "MODE: GUIDE — no active event space. You may chat, get to know them, answer app questions and remember "
             "tastes they volunteer. You must NOT plan or recommend anything until an event space exists: create one "
             "(create_event) as soon as they tell you what they're planning.",
    "setup": "MODE: SETUP — an event space exists but some details are missing. Collect them gently, one at a time.",
    "planner": "MODE: PLANNER — the event is ready. Plan, refine and be their companion.",
}


def _facts(items, limit=30):
    items = sorted(items, key=lambda f: (-f.get("confidence", 0), f.get("updated_at", "")))[:limit]
    return "; ".join(f"{'♥' if f.get('sentiment', 0) > 0 else '✗'} {f['category']}: {f['text']}" for f in items) or "none yet"


def build_system(s: Snapshot, voice: bool = False) -> str:
    u = s.user
    prof = u.get("profile") or {}
    first = (u.get("name") or "").split(" ")[0]
    parts = [BASE]
    if voice:
        parts.append(VOICE)
    now = local_now()
    lines = [f"# LIVE CONTEXT\nTODAY: {now.strftime('%A, %d %B %Y')} ({now.date().isoformat()}), local time {now.strftime('%H:%M')}",
             MODE_RULES[s.mode],
             f"USER: {u.get('name')} (call them {first})" + ("" if u.get("name_confirmed") or u.get("name_from_provider") else
                                                             " — name was guessed from email; confirm what to call them when natural"),
             f"RELATIONSHIP: {s.couple.get('status', 'engaged')}",
             f"PARTNER: {s.partner.get('name') + ' (has joined the app)' if s.partner else (prof.get('partner_name') or 'name unknown') + ' (not joined yet)'}"]
    pf = {k: v for k, v in prof.items() if k not in ("greeted", "invite_offered", "partner_hints") and v}
    if pf:
        lines.append(f"PROFILE (already known — don't re-ask): {pf}")
    if prof.get("partner_hints"):
        lines.append(f"WHAT {first.upper()} TOLD YOU ABOUT THE PARTNER: {prof['partner_hints'][-10:]}")
    if s.conv.get("summary"):
        lines.append(f"STORY SO FAR: {s.conv['summary']}")
    if s.space:
        sp_ = s.space
        fields = {k: sp_.get(k) for k in sp.FIELD_META if sp_.get(k) not in (None, "", [])}
        lines.append(f"ACTIVE EVENT: {sp_['title']} ({sp_['type']}), state={sp_.get('state')}, details={fields}, "
                     f"missing={sp_['missing_fields']}, plan={'yes v' + str(sp_.get('active_plan_version')) if sp_.get('active_plan_version') else 'not yet'}")
        lines.append(SKILLS[sp_["type"]])
    others = [f"{x['title']} ({x['type']}, id={x['id']})" for x in s.spaces if not s.space or x["id"] != s.space["id"]]
    if others:
        lines.append("OTHER EVENTS: " + "; ".join(others[:8]))
    lines.append(f"{first.upper()}'S TASTES: {_facts(s.my_facts)}")
    lines.append(f"TASTE COVERAGE: {coverage(s.my_facts)}")
    if s.partner:
        lines.append(f"{s.partner.get('name', 'PARTNER').upper()}'S SHARED TASTES: {_facts(s.partner_facts, 25)}")
    dna = s.couple.get("dna") or {}
    if dna.get("vibe"):
        lines.append(f"COUPLE VIBE: {dna['vibe']}. Shared loves: {', '.join(x['name'] for x in dna.get('shared', [])[:10])}")
    if s.decisions:
        lines.append("DECISIONS: " + " | ".join(d["summary"] for d in s.decisions[:8]))
    if s.episodes:
        lines.append("PAST EXPERIENCES (bring up naturally when relevant): " + " | ".join(
            f"{e.get('summary')} (loved {e.get('highlights')}, disliked {e.get('lowlights')})" for e in s.episodes))
    n = s.next
    lines.append(f"# YOUR NEXT MOVE (stage: {n.get('stage')})\n{n.get('goal')}\nAvoid: " + "; ".join(n.get("avoid", [])))
    parts.append("\n".join(lines))
    return "\n\n".join(parts)
