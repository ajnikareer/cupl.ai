import os
import re

cols = set()
for root, dirs, files in os.walk("backend/app"):
    for f in files:
        if f.endswith(".py"):
            content = open(os.path.join(root, f), encoding="utf-8").read()
            for m in re.findall(r'collection\(["\']([^"\']+)["\']\)', content):
                cols.add(m)
            for m in re.findall(r'document\(["\']([^/"\']+)/', content):
                cols.add(m)
print("Collections found:", sorted(cols))

