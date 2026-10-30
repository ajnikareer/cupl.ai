with open('frontend/src/pages/Login.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

old_tok = 'localStorage.setItem("ww_dev_token", "dev-cupl_star_1");'
new_tok = '''localStorage.removeItem("ww_chat_history");
                localStorage.setItem("ww_dev_token", "dev-groom_narayan");'''

if old_tok in c:
    c = c.replace(old_tok, new_tok)
    c = c.replace('<span>1-Click Demo: Explore as Narayan</span>', '<span>1-Click Groom Demo (Narayan)</span>')
    with open('frontend/src/pages/Login.tsx', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Updated Login.tsx with groom_narayan successfully!")
else:
    print("old_tok not found in Login.tsx")
