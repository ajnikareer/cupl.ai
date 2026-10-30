import os

# 1. Update frontend/src/components/ui.tsx
with open("frontend/src/components/ui.tsx", "r", encoding="utf-8") as f:
    ui_content = f.read()

# Replace CuplMark, HeartMark, Logo, Avatar
old_block = ui_content[ui_content.find("export const CuplMark"):ui_content.find("export const PageTitle")]

new_block = """export const CuplMark = ({ className = "h-9 w-9" }: { className?: string }) => (
  <img
    src="/img/avatar.png"
    alt="cupl.ai"
    className={clsx("rounded-xl object-contain shrink-0", className)}
  />
);

export const HeartMark = CuplMark;

export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
  <div className={clsx("flex items-center", className)}>
    <img
      src="/img/cupl_logo.png"
      alt="cupl.ai — Your AI concierge for life together"
      className={clsx(
        "w-auto rounded-xl object-contain shadow-2xs transition",
        small ? "h-9 max-w-[170px]" : "h-11 md:h-12 max-w-[230px]"
      )}
    />
  </div>
);

export const Avatar = ({ size = 40, ring = false, className = "" }: { size?: number; ring?: boolean; className?: string }) => (
  <div className={clsx("relative shrink-0", className)} style={{ width: size, height: size }}>
    {ring && <span className="ring-pulse absolute inset-0 rounded-full border-2 border-brand" />}
    <img src="/img/avatar.png" alt="cupl AI" className="h-full w-full rounded-full object-cover shadow-sm" />
  </div>
);

"""

if old_block:
    ui_updated = ui_content.replace(old_block, new_block)
    with open("frontend/src/components/ui.tsx", "w", encoding="utf-8", newline="") as f:
        f.write(ui_updated)
    print("Updated ui.tsx")
else:
    print("Could not find old_block in ui.tsx")

# 2. Update frontend/src/pages/ChatPage.tsx
with open("frontend/src/pages/ChatPage.tsx", "r", encoding="utf-8") as f:
    chat_content = f.read()
chat_updated = chat_content.replace('src="/img/avatar.jpg"', 'src="/img/avatar.png"')
with open("frontend/src/pages/ChatPage.tsx", "w", encoding="utf-8", newline="") as f:
    f.write(chat_updated)
print("Updated ChatPage.tsx")

# 3. Update frontend/src/chat/VoiceOverlay.tsx
with open("frontend/src/chat/VoiceOverlay.tsx", "r", encoding="utf-8") as f:
    voice_content = f.read()
voice_updated = voice_content.replace('src="/img/avatar.jpg"', 'src="/img/avatar.png"')
with open("frontend/src/chat/VoiceOverlay.tsx", "w", encoding="utf-8", newline="") as f:
    f.write(voice_updated)
print("Updated VoiceOverlay.tsx")

