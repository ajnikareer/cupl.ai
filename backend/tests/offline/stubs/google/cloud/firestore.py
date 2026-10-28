"""In-memory async Firestore fake (enough for WeaveWed tests)."""
import copy

STORE: dict = {}


class _Snap:
    def __init__(self, path, data):
        self._path, self._data = path, data
        self.id = path.split("/")[-1]
        self.exists = data is not None
        self.reference = _Doc(path)

    def to_dict(self):
        return copy.deepcopy(self._data) if self._data is not None else None


class _Doc:
    def __init__(self, path):
        self.path = path
        self.id = path.split("/")[-1]

    async def get(self):
        return _Snap(self.path, STORE.get(self.path))

    async def set(self, data, merge=False):
        if merge and self.path in STORE:
            _deep_merge(STORE[self.path], copy.deepcopy(data))
        else:
            STORE[self.path] = copy.deepcopy(data)

    async def update(self, data):
        if self.path not in STORE:
            raise KeyError(f"No document to update: {self.path}")
        for k, v in data.items():
            STORE[self.path][k] = copy.deepcopy(v)

    async def delete(self):
        STORE.pop(self.path, None)


def _deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            _deep_merge(a[k], v)
        else:
            a[k] = v


class _Query:
    def __init__(self, col, filters=None, order=None, lim=None):
        self.col, self.filters, self.order, self.lim = col, filters or [], order, lim

    def where(self, field=None, op=None, value=None, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return _Query(self.col, self.filters + [(field, op, value)], self.order, self.lim)

    def order_by(self, field, direction="ASCENDING"):
        return _Query(self.col, self.filters, (field, direction), self.lim)

    def limit(self, n):
        return _Query(self.col, self.filters, self.order, n)

    def find_nearest(self, **kw):
        raise RuntimeError("vector index missing (fake)")

    async def stream(self):
        pre = self.col + "/"
        rows = [(p, d) for p, d in STORE.items() if p.startswith(pre) and "/" not in p[len(pre):]]
        def ok(d):
            for f, op, v in self.filters:
                x = d.get(f)
                if op == "==" and x != v: return False
                if op == ">" and not (x is not None and x > v): return False
                if op == "in" and x not in v: return False
            return True
        rows = [r for r in rows if ok(r[1])]
        if self.order:
            rows.sort(key=lambda r: r[1].get(self.order[0]) or "", reverse=self.order[1] == "DESCENDING")
        if self.lim:
            rows = rows[: self.lim]
        for p, d in rows:
            yield _Snap(p, d)


class _Col(_Query):
    def __init__(self, path):
        super().__init__(path)

    def document(self, i):
        return _Doc(f"{self.col}/{i}")


class AsyncClient:
    def __init__(self, *a, **k):
        pass

    def document(self, path):
        return _Doc(path)

    def collection(self, path):
        return _Col(path)
