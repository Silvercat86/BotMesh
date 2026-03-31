from .utils import normalize_name, make_external_id


def people_to_payload(people):
    result = []

    for p in people:

        if not p.fio or not p.fio.strip():
            continue

        external_id = make_external_id(
            p.source,
            p.fio,
            p.phone,
            p.email
        )

        result.append({
            "full_name": p.fio.strip(),
            "normalized_name": normalize_name(p.fio),

            "telegram": p.username,
            "email": p.email,
            "phone": p.phone,

            "birthday": p.birthday.isoformat() if p.birthday else None,
            "start_date": p.start_date.isoformat() if p.start_date else None,

            "external_id": external_id,
        })

    return result