with open('frontend/src/pages/SpaceView.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace Link with button onClick={() => nav("/app/chat")}
target_btn = '''<Link to="/app/chat" className="btn-primary w-full sm:w-auto px-6 py-2.5 flex items-center justify-center gap-2 shadow-sm">
              <span>💌</span> Invite Bride in Chat
            </Link>'''

replacement_btn = '''<button type="button" onClick={() => nav("/app/chat")} className="btn-primary w-full sm:w-auto px-6 py-2.5 flex items-center justify-center gap-2 shadow-sm">
              <span>💌</span> Invite Bride in Chat
            </button>'''

c = c.replace(target_btn, replacement_btn)

# Replace user?.displayName with me?.user?.name
target_user = "{user?.displayName ? `${user.displayName.split(\" \")[0]}, your` : \"Your\"}"
replacement_user = "{me?.user?.name ? `${me.user.name.split(\" \")[0]}, your` : \"Your\"}"
c = c.replace(target_user, replacement_user)

with open('frontend/src/pages/SpaceView.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("SpaceView.tsx fixed successfully!")
