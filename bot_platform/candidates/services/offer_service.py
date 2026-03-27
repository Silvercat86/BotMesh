from django.db import transaction
from django.utils import timezone

from candidates.models import Candidate, Employee, Offer, OfferResponse
from communication.models import Notification
from events.models import Event


class OfferServiceError(Exception):
    pass


class OfferNotFound(OfferServiceError):
    pass


class InvalidOfferState(OfferServiceError):
    pass


def create_offer(
    *,
    company,
    full_name: str,
    text: str,
    created_by=None,
    telegram_user=None,
) -> Offer:
    with transaction.atomic():
        candidate = Candidate.objects.create(
            company=company,
            full_name=full_name,
            telegram_user=telegram_user,
        )

        offer = Offer.objects.create(
            company=company,
            candidate=candidate,
            text=text,
            created_by=created_by,
            status=Offer.Status.DRAFT,
        )

        Event.objects.create(
            type="offer_created",
            entity_type="offer",
            entity_id=offer.id,
            payload={
                "offer_id": offer.id,
                "candidate_id": candidate.id,
                "full_name": full_name,
            },
        )

        return offer


def mark_offer_sent(*, offer: Offer) -> Offer:
    if offer.status != Offer.Status.DRAFT:
        raise InvalidOfferState("Only draft offer can be sent")

    offer.status = Offer.Status.SENT
    offer.save(update_fields=["status", "updated_at"])

    Event.objects.create(
        type="offer_sent",
        entity_type="offer",
        entity_id=offer.id,
        payload={"offer_id": offer.id},
    )

    if offer.candidate.telegram_user_id:
        Notification.objects.create(
            user=offer.candidate.telegram_user,
            type=Notification.Type.OFFER,
            channel=Notification.Channel.TELEGRAM,
            send_at=timezone.now(),
            payload={
                "offer_id": offer.id,
                "text": offer.text,
            },
        )

    return offer


def accept_offer(*, offer: Offer) -> Employee:
    if offer.status not in [Offer.Status.SENT, Offer.Status.DISCUSS]:
        raise InvalidOfferState("Only sent/discuss offer can be accepted")

    with transaction.atomic():
        employee = (
            Employee.objects.filter(
                company=offer.company,
                telegram_user=offer.candidate.telegram_user,
            ).first()
            if offer.candidate.telegram_user_id
            else None
        )

        if not employee:
            employee = Employee.objects.filter(
                company=offer.company,
                full_name=offer.candidate.full_name,
            ).first()

        if not employee:
            employee = Employee.objects.create(
                company=offer.company,
                full_name=offer.candidate.full_name,
                telegram_user=offer.candidate.telegram_user,
            )
        else:
            changed = []

            if not employee.telegram_user_id and offer.candidate.telegram_user_id:
                employee.telegram_user = offer.candidate.telegram_user
                changed.append("telegram_user")

            if changed:
                employee.save(update_fields=changed)

        OfferResponse.objects.get_or_create(
            offer=offer,
            type=OfferResponse.Type.ACCEPT,
        )

        offer.status = Offer.Status.ACCEPTED
        offer.employee = employee
        offer.save(update_fields=["status", "employee", "updated_at"])

        Event.objects.create(
            type="offer_accepted",
            entity_type="offer",
            entity_id=offer.id,
            payload={
                "offer_id": offer.id,
                "employee_id": employee.id,
            },
        )

        return employee


def discuss_offer(*, offer: Offer) -> Offer:
    if offer.status not in [Offer.Status.SENT, Offer.Status.DRAFT]:
        raise InvalidOfferState("Offer cannot be moved to discuss from current status")

    with transaction.atomic():
        OfferResponse.objects.get_or_create(
            offer=offer,
            type=OfferResponse.Type.DISCUSS,
        )

        offer.status = Offer.Status.DISCUSS
        offer.save(update_fields=["status", "updated_at"])

        Event.objects.create(
            type="offer_discuss_requested",
            entity_type="offer",
            entity_id=offer.id,
            payload={"offer_id": offer.id},
        )

        return offer


def reject_offer(*, offer: Offer) -> Offer:
    if offer.status not in [Offer.Status.SENT, Offer.Status.DISCUSS]:
        raise InvalidOfferState("Only sent/discuss offer can be rejected")

    with transaction.atomic():
        OfferResponse.objects.get_or_create(
            offer=offer,
            type=OfferResponse.Type.REJECT,
        )

        offer.status = Offer.Status.REJECTED
        offer.save(update_fields=["status", "updated_at"])

        Event.objects.create(
            type="offer_rejected",
            entity_type="offer",
            entity_id=offer.id,
            payload={"offer_id": offer.id},
        )

        return offer