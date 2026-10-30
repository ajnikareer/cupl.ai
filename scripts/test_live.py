import httpx
import re

html = httpx.get("https://weavewed-v2-sem5hyzlrq-uc.a.run.app/").text
scripts = re.findall(r'src="([^"]+)"', html)
print("scripts:", scripts)
js = httpx.get("https://weavewed-v2-sem5hyzlrq-uc.a.run.app" + scripts[0]).text
print("Has Audit Dashboard in bundle?:", "QLOO Taste Intelligence" in js)
print("Has QLOO Intelligence Dashboard link?:", "QLOO Intelligence Dashboard" in js)
print("Has Create account to join?:", "Create account to join" in js)
