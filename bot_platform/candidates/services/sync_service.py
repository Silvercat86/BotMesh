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


def should_update(old, new):
    return new is not None and old != new


def find_employee(company, data, telegram_user):
    external_id = data.get("external_id")
    email = data.get("email")
    phone = data.get("phone")
    normalized_name = data.get("normalized_name")

    # 1. external_id
    if external_id:
        emp = Employee.objects.filter(
            company=company,
            external_id=external_id
        ).first()
        if emp:
            return emp

    # 2. telegram
    if telegram_user:
        emp = Employee.objects.filter(
            company=company,
            telegram_user=telegram_user
        ).first()
        if emp:
            return emp

    # 3. email
    if email:
        emp = Employee.objects.filter(
            company=company,
            email=email
        ).first()
        if emp:
            return emp

    # 4. phone
    if phone:
        emp = Employee.objects.filter(
            company=company,
            phone=phone
        ).first()
        if emp:
            return emp

    # 5. normalized_name
    if normalized_name:
        emp = Employee.objects.filter(
            company=company,
            normalized_name=normalized_name
        ).first()
        if emp:
            return emp

    return None


@transaction.atomic
def sync_employees(company, employees_data: list):

    results = {
        "created": 0,
        "updated": 0,
        "processed": len(employees_data)
    }

    incoming_ids = set()

    for data in employees_data:

        full_name = data.get("full_name")
        normalized_name = data.get("normalized_name")

        external_id = data.get("external_id")
        telegram_username = data.get("telegram")
        email = data.get("email")
        phone = data.get("phone")

        birthday = parse_date(data.get("birthday"))
        start_date = parse_date(data.get("start_date"))

        if external_id:
            incoming_ids.add(external_id)

        telegram_user = get_or_create_telegram(telegram_username)

        employee = find_employee(company, data, telegram_user)

        # CREATE
        if not employee:
            employee = Employee.objects.create(
                company=company,
                full_name=full_name,
                normalized_name=normalized_name,

                telegram_user=telegram_user,
                email=email,
                phone=phone,

                birthday=birthday,
                start_date=start_date,
                external_id=external_id,
                is_active=True,
            )

            results["created"] += 1

            Event.objects.create(
                type="employee_created_from_sync",
                entity_type="employee",
                entity_id=employee.id,
                payload={"full_name": full_name}
            )

            continue

        # UPDATE
        changed = []

        if external_id and employee.external_id != external_id:
            employee.external_id = external_id
            changed.append("external_id")

        if telegram_user and employee.telegram_user != telegram_user:
            employee.telegram_user = telegram_user
            changed.append("telegram_user")

        if should_update(employee.email, email):
            employee.email = email
            changed.append("email")

        if should_update(employee.phone, phone):
            employee.phone = phone
            changed.append("phone")

        if should_update(employee.birthday, birthday):
            employee.birthday = birthday
            changed.append("birthday")

        if should_update(employee.start_date, start_date):
            employee.start_date = start_date
            changed.append("start_date")

        if normalized_name and employee.normalized_name != normalized_name:
            employee.normalized_name = normalized_name
            changed.append("normalized_name")

        if changed:
            employee.save(update_fields=changed)
            results["updated"] += 1

            Event.objects.create(
                type="employee_updated_from_sync",
                entity_type="employee",
                entity_id=employee.id,
                payload={"fields": changed}
            )

    # SOFT DELETE
    existing = Employee.objects.filter(company=company)

    for emp in existing:
        if emp.external_id and emp.external_id not in incoming_ids:
            if emp.is_active:
                emp.is_active = False
                emp.save(update_fields=["is_active"])

    return results