def verify_id_token(t):
    if t.startswith("tok-"):
        uid = t[4:]
        return {"uid": uid, "name": uid.title(), "email": uid + "@x.com", "exp": 9999999999}
    raise ValueError("bad token")
