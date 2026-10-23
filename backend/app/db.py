import asyncio
import secrets

from google.cloud import firestore

from .config import settings
from .core.timeutil import now_iso  # noqa: F401  (re-export)

db = firestore.AsyncClient(project=settings.GCP_PROJECT or None, database=settings.FIRESTORE_DB)


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def doc_dict(snap) -> dict | None:
    if snap is None or not snap.exists:
        return None
    d = snap.to_dict() or {}
    d["id"] = snap.id
    d.pop("embedding", None)
    return d


async def get_doc(path: str) -> dict | None:
    return doc_dict(await db.document(path).get())


async def get_docs(*paths: str) -> list[dict | None]:
    return list(await asyncio.gather(*[get_doc(p) for p in paths]))


async def list_col(col_ref, limit: int | None = None) -> list[dict]:
    q = col_ref.limit(limit) if limit else col_ref
    return [d for d in [doc_dict(s) async for s in q.stream()] if d]
