class _Obj:
    def __init__(self, *a, **k):
        self.__dict__.update(k)
    def __repr__(self): return f"{type(self).__name__}({self.__dict__})"
def __getattr__(name):
    if name in ("StartSensitivity", "EndSensitivity", "Modality"):
        class E:
            def __getattr__(s, n): return n
        return E()
    return type(name, (_Obj,), {})
class Part(_Obj):
    @staticmethod
    def from_function_response(name, response): return Part(function_response={"name": name, "response": response})
