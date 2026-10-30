import asyncio
import os
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.config import settings
settings.QLOO_API_KEY = "hack_2e9a0b569f352f79299887692053d2cae44c293c"

from backend.app.services import qloo

async def test_qloo():
    # 1. Search places in Hyderabad
    print("=== SEARCH QLOO PLACES HYDERABAD ===")
    places = await qloo.insights(qloo.PLACE, location="Hyderabad", take=15)
    for p in places:
        print(f"Name: {p.get('name')} | Category: {p.get('category')} | Tags: {p.get('tags')}")

    # 2. Search brands
    print("\n=== SEARCH QLOO BRANDS ===")
    brands = await qloo.insights(qloo.BRAND, take=10)
    for b in brands:
        print(f"Brand: {b.get('name')} | Category: {b.get('category')} | Tags: {b.get('tags')}")

asyncio.run(test_qloo())
