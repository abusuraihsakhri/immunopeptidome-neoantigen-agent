"""Strict CSV boolean parsing shared by both command-line interfaces."""


def parse_csv_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in ("true", "1", "yes", "y", "on"):
        return True
    if normalized in ("false", "0", "no", "n", "off", ""):
        return False
    raise ValueError("Invalid is_critical_flag: expected true/false, yes/no, or 1/0")
