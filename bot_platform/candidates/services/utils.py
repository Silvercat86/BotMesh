import hashlib


def normalize_name(name: str | None) -> str | None:
    if not name:
        return None
    return " ".join(name.strip().lower().split())


def make_external_id(source: str, fio: str | None, phone: str | None, email: str | None) -> str | None:
    if not fio:
        return None

    base = f"{normalize_name(fio)}|{phone or ''}|{email or ''}"
    hash_id = hashlib.md5(base.encode()).hexdigest()

    return f"{source}:{hash_id}"