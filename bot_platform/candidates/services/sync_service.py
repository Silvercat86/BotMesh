from django.db import transaction
from datetime import datetime

from candidates.models import Employee
from accounts.models import TelegramUser
from events.models import Event


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except:
        return None


def get_or_create_telegram(username: str):
    if not username:
        return None

    username = username.lstrip("@")

    user = TelegramUser.objects.filter(username=username).first()

    if user:
        return user

    return TelegramUser.objects.create(
        username=username,
        first_name=username,
        is_placeholder=True
    )


@transaction.atomic
def sync_employees(company, employees_data: list):

    results = {
        "created": 0,
        "updated": 0,
        "processed": len(employees_data)
    }

    for data in employees_data:

        full_name = data.get("full_name")
        external_id = data.get("external_id")
        telegram_username = data.get("telegram")

        birthday = parse_date(data.get("birthday"))
        start_date = parse_date(data.get("start_date"))

        telegram_user = get_or_create_telegram(telegram_username)

        employee = None

        # ✅ 1. главный ключ
        if external_id:
            employee = Employee.objects.filter(
                company=company,
                external_id=external_id
            ).first()

        # ✅ 2. telegram fallback
        if not employee and telegram_user:
            employee = Employee.objects.filter(
                company=company,
                telegram_user=telegram_user
            ).first()

        if not employee:
            employee = Employee.objects.create(
                company=company,
                full_name=full_name,
                telegram_user=telegram_user,
                birthday=birthday,
                start_date=start_date,
                external_id=external_id,
            )

            results["created"] += 1

            Event.objects.create(
                type="employee_created_from_sync",
                entity_type="employee",
                entity_id=employee.id,
                payload={"full_name": full_name}
            )

            continue

        changed = []

        if external_id and employee.external_id != external_id:
            employee.external_id = external_id
            changed.append("external_id")

        if telegram_user and not employee.telegram_user:
            employee.telegram_user = telegram_user
            changed.append("telegram_user")

        if birthday and employee.birthday != birthday:
            employee.birthday = birthday
            changed.append("birthday")

        if start_date and employee.start_date != start_date:
            employee.start_date = start_date
            changed.append("start_date")

        if changed:
            employee.save(update_fields=changed)
            results["updated"] += 1

            Event.objects.create(
                type="employee_updated_from_sync",
                entity_type="employee",
                entity_id=employee.id,
                payload={"fields": changed}
            )

    return results