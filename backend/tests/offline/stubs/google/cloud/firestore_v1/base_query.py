class FieldFilter:
    def __init__(self, field_path, op_string, value):
        self.field_path, self.op_string, self.value = field_path, op_string, value
