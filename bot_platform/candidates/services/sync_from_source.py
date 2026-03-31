from django.conf import settings

from candidates.services.people_directory import PeopleDirectoryService
from candidates.services.payload_builder import people_to_payload
from candidates.services.sync_service import sync_employees


def build_people_service():
    return PeopleDirectoryService(
        sources=settings.PEOPLE_SOURCES,
        cache_ttl=300,
    )


def sync_from_people_service(company):

    people_service = build_people_service()

    all_people = []

    for source in settings.PEOPLE_SOURCES.keys():
        people = people_service.get_people(source)
        all_people.extend(people)

    payload = people_to_payload(all_people)

    return sync_employees(company, payload)