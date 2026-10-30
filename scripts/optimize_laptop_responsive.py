# 1. Update frontend/src/components/ui.tsx
with open("frontend/src/components/ui.tsx", "r", encoding="utf-8") as f:
    ui = f.read()

old_logo = '''export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
  <div className={clsx("flex items-center", className)}>
    <img
      src="/img/cupl_logo.png"
      alt="cupl.ai — Your AI concierge for life together"
      className={clsx(
        "rounded-xl object-contain shadow-2xs transition",
        small ? "h-10 md:h-11 w-auto max-w-[190px]" : "w-full max-w-[240px] h-auto max-h-[88px]"
      )}
    />
  </div>
);'''

new_logo = '''export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
  <div className={clsx("flex items-center", className)}>
    <img
      src="/img/cupl_logo.png"
      alt="cupl.ai — Your AI concierge for life together"
      className={clsx(
        "rounded-xl object-contain shadow-2xs transition",
        small ? "h-8 max-w-[140px]" : "h-9 xl:h-10 w-auto max-w-[170px] xl:max-w-[200px]"
      )}
    />
  </div>
);'''

ui_norm = ui.replace("\r\n", "\n")
old_logo_norm = old_logo.replace("\r\n", "\n")
new_logo_norm = new_logo.replace("\r\n", "\n")

if old_logo_norm in ui_norm:
    ui_updated = ui_norm.replace(old_logo_norm, new_logo_norm)
    if "\r\n" in ui:
        ui_updated = ui_updated.replace("\n", "\r\n")
    with open("frontend/src/components/ui.tsx", "w", encoding="utf-8", newline="") as f:
        f.write(ui_updated)
    print("Updated ui.tsx logo size")
else:
    print("Could not find old_logo in ui.tsx")


# 2. Update frontend/src/components/Layout.tsx
with open("frontend/src/components/Layout.tsx", "r", encoding="utf-8") as f:
    layout = f.read()

layout_norm = layout.replace("\r\n", "\n")

# Sidebar width & padding
# <aside className="sticky top-0 hidden h-screen w-[272px] shrink-0 flex-col border-r border-line bg-white/80 p-5 lg:flex">
old_aside = '<aside className="sticky top-0 hidden h-screen w-[272px] shrink-0 flex-col border-r border-line bg-white/80 p-5 lg:flex">'
new_aside = '<aside className="sticky top-0 hidden h-screen w-[220px] xl:w-[250px] shrink-0 flex-col border-r border-line bg-white/80 p-3.5 xl:p-5 lg:flex">'

old_nav_items = 'className={({ isActive }) => clsx("flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition",'
new_nav_items = 'className={({ isActive }) => clsx("flex items-center gap-2.5 xl:gap-3 rounded-2xl px-2.5 py-2 xl:px-3 xl:py-2.5 text-xs xl:text-sm transition",'

if old_aside in layout_norm:
    layout_norm = layout_norm.replace(old_aside, new_aside)
    layout_norm = layout_norm.replace(old_nav_items, new_nav_items)
    if "\r\n" in layout:
        layout_norm = layout_norm.replace("\n", "\r\n")
    with open("frontend/src/components/Layout.tsx", "w", encoding="utf-8", newline="") as f:
        f.write(layout_norm)
    print("Updated Layout.tsx sidebar dimensions")
else:
    print("Could not find old_aside in Layout.tsx")


# 3. Update frontend/src/pages/ChatPage.tsx
with open("frontend/src/pages/ChatPage.tsx", "r", encoding="utf-8") as f:
    chat = f.read()

chat_norm = chat.replace("\r\n", "\n")

# 3A: Chat History Drawer
old_drawer = 'className="w-[15%] min-w-[210px] max-w-[250px] shrink-0 border-r border-line bg-white flex flex-col h-full z-10 select-none"'
new_drawer = 'className="w-[180px] xl:w-[220px] shrink-0 border-r border-line bg-white flex flex-col h-full z-10 select-none"'

# 3B: Middle Chat Column
old_mid = '<section className="flex flex-1 min-w-[320px] flex-col border-r border-line bg-white h-full overflow-hidden">'
new_mid = '<section className="flex flex-1 min-w-0 flex-col border-r border-line bg-white h-full overflow-hidden">'

# 3C: Companion Stage Section
old_stage = '<section className="hidden md:flex flex-1 min-w-[340px] flex-col bg-gradient-to-b from-[#fff8f6] via-blush/35 to-[#fcecee] h-full overflow-y-auto px-5 py-6 justify-between relative">'
new_stage = '<section className="hidden md:flex w-[280px] xl:w-[330px] shrink-0 flex-col bg-gradient-to-b from-[#fff8f6] via-blush/35 to-[#fcecee] h-full overflow-y-auto px-4 py-4 xl:px-5 xl:py-6 justify-between relative">'

# 3D: Avatar Size in Companion Stage
old_avatar = 'className={clsx(\n                "relative h-36 w-36 xl:h-44 xl:w-44 rounded-full border-4 border-white object-cover shadow-soft transition-all duration-300",\n                voice !== "off" ? "scale-105" : "grayscale-[10%]"\n              )}'
new_avatar = 'className={clsx(\n                "relative h-28 w-28 xl:h-36 xl:w-36 rounded-full border-4 border-white object-cover shadow-soft transition-all duration-300",\n                voice !== "off" ? "scale-105" : "grayscale-[10%]"\n              )}'

# 3E: Stage center gap
old_gap = '<div className="flex flex-col items-center justify-center gap-6 my-auto py-4">'
new_gap = '<div className="flex flex-col items-center justify-center gap-3 xl:gap-5 my-auto py-2">'

# 3F: Buttons in stage
old_btn_couple = 'className={clsx(\n              "flex h-12 items-center gap-2 rounded-full px-5 text-xs font-semibold border transition shadow-soft",'
new_btn_couple = 'className={clsx(\n              "flex h-10 xl:h-11 items-center gap-1.5 xl:gap-2 rounded-full px-3.5 xl:px-4 text-[11px] xl:text-xs font-semibold border transition shadow-soft",'

old_btn_call = 'className="flex h-12 items-center gap-2 rounded-full bg-brand px-6 text-xs font-semibold text-white shadow-soft hover:bg-brand/90 transition"'
new_btn_call = 'className="flex h-10 xl:h-11 items-center gap-1.5 xl:gap-2 rounded-full bg-brand px-4 xl:px-5 text-[11px] xl:text-xs font-semibold text-white shadow-soft hover:bg-brand/90 transition"'

chat_norm = chat_norm.replace(old_drawer, new_drawer)
chat_norm = chat_norm.replace(old_mid, new_mid)
chat_norm = chat_norm.replace(old_stage, new_stage)
chat_norm = chat_norm.replace(old_avatar, new_avatar)
chat_norm = chat_norm.replace(old_gap, new_gap)
chat_norm = chat_norm.replace(old_btn_couple, new_btn_couple)
chat_norm = chat_norm.replace(old_btn_call, new_btn_call)

if "\r\n" in chat:
    chat_norm = chat_norm.replace("\n", "\r\n")

with open("frontend/src/pages/ChatPage.tsx", "w", encoding="utf-8", newline="") as f:
    f.write(chat_norm)
print("Updated ChatPage.tsx responsive laptop layout")
