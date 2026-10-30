with open('frontend/src/auth/AuthProvider.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

target = 'setUser({ uid: devTok.replace("dev-", ""), displayName: devTok.includes("narayan") ? "Narayan" : "Amruta", email: `${devTok}@cupl.app` });'
replacement = '''const uid = devTok.replace("dev-", "");
      const isAmruta = uid.endsWith("_2") || uid.includes("amruta") || uid.includes("vyawahare");
      const name = isAmruta ? "Amruta" : "Narayan";
      setUser({ uid, displayName: name, email: `${devTok}@cupl.app` });'''

if target in c:
    c = c.replace(target, replacement)
    with open('frontend/src/auth/AuthProvider.tsx', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Updated AuthProvider.tsx successfully!")
else:
    print("Target not found in AuthProvider.tsx")
