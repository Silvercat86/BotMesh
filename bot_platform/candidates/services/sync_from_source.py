from candidates.services.people_directory import PeopleDirectoryService
from candidates.services.sync_service import sync_employees

from django.conf import settings


def build_people_service():
    return PeopleDirectoryService(
        sources=settings.PEOPLE_SOURCES,
        cache_ttl=300,
    )




def people_to_payload(people):
    result = []

    for p in people:

        if not p.fio or not p.fio.strip():
            continue

        row_id = p.extra_data.get("__row_id__")

        external_id = None
        if row_id:
            external_id = f"{p.source}:{row_id}"
        else:
            external_id = f"{p.source}:{p.fio}"

        result.append({
            "full_name": p.fio.strip(),
            "telegram": p.username,
            "birthday": p.birthday.isoformat() if p.birthday else None,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "external_id": external_id
        })

    return result


def sync_from_people_service(company):

    people_service = build_people_service()

    all_people = []

    for source in settings.PEOPLE_SOURCES.keys():
        people = people_service.get_people(source)
        all_people.extend(people)

    payload = people_to_payload(all_people)

    return sync_employees(company, payload)