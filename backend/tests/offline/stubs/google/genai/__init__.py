from . import types
class _Models:
    async def generate_content(self, **k): raise RuntimeError("stub: no gemini")
    async def generate_content_stream(self, **k): raise RuntimeError("stub: no gemini")
    async def embed_content(self, **k): raise RuntimeError("stub: no embeddings")
class _Aio:
    models = _Models()
class Client:
    def __init__(self, *a, **k): self.aio = _Aio()
