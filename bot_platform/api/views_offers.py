from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from accounts.models import TelegramUser
from candidates.models import Offer
from candidates.services.offer_service import (
    create_offer,
    mark_offer_sent,
    accept_offer,
    discuss_offer,
    reject_offer,
    OfferServiceError,
    InvalidOfferState,
)


def _serialize_offer(offer: Offer) -> dict:
    return {
        "id": offer.id,
        "status": offer.status,
        "company_id": offer.company_id,
        "candidate": {
            "id": offer.candidate_id,
            "full_name": offer.candidate.full_name,
            "telegram_user_id": offer.candidate.telegram_user_id,
        },
        "employee_id": offer.employee_id,
        "text": offer.text,
        "created_by_id": offer.created_by_id,
        "created_at": offer.created_at,
        "updated_at": offer.updated_at,
    }


@api_view(["POST"])
def create_offer_view(request):
    full_name = request.data.get("full_name")
    text = request.data.get("text")
    telegram_id = request.data.get("telegram_id")

    if not full_name or not text:
        return Response(
            {"error": "full_name and text are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    telegram_user = None
    if telegram_id:
        telegram_user = TelegramUser.objects.filter(
            telegram_id=telegram_id
        ).first()

    offer = create_offer(
        company=request.company,
        full_name=full_name,
        text=text,
        created_by=getattr(request, "user", None) if getattr(request, "user", None) and request.user.is_authenticated else None,
        telegram_user=telegram_user,
    )

    return Response(_serialize_offer(offer), status=status.HTTP_201_CREATED)


@api_view(["POST"])
def send_offer_view(request, offer_id: int):
    offer = Offer.objects.filter(company=request.company, id=offer_id).select_related(
        "candidate", "employee", "company", "created_by"
    ).first()
    if not offer:
        return Response({"error": "offer not found"}, status=404)

    try:
        offer = mark_offer_sent(offer=offer)
    except InvalidOfferState as e:
        return Response({"error": str(e)}, status=400)

    return Response(_serialize_offer(offer))


@api_view(["POST"])
def accept_offer_view(request, offer_id: int):
    offer = Offer.objects.filter(company=request.company, id=offer_id).select_related(
        "candidate", "employee", "company", "created_by"
    ).first()
    if not offer:
        return Response({"error": "offer not found"}, status=404)

    try:
        employee = accept_offer(offer=offer)
    except InvalidOfferState as e:
        return Response({"error": str(e)}, status=400)

    return Response({
        "offer_id": offer.id,
        "status": Offer.Status.ACCEPTED,
        "employee": {
            "id": employee.id,
            "full_name": employee.full_name,
            "telegram_user_id": employee.telegram_user_id,
        }
    })


@api_view(["POST"])
def discuss_offer_view(request, offer_id: int):
    offer = Offer.objects.filter(company=request.company, id=offer_id).select_related(
        "candidate", "employee", "company", "created_by"
    ).first()
    if not offer:
        return Response({"error": "offer not found"}, status=404)

    try:
        offer = discuss_offer(offer=offer)
    except InvalidOfferState as e:
        return Response({"error": str(e)}, status=400)

    return Response(_serialize_offer(offer))


@api_view(["POST"])
def reject_offer_view(request, offer_id: int):
    offer = Offer.objects.filter(company=request.company, id=offer_id).select_related(
        "candidate", "employee", "company", "created_by"
    ).first()
    if not offer:
        return Response({"error": "offer not found"}, status=404)

    try:
        offer = reject_offer(offer=offer)
    except InvalidOfferState as e:
        return Response({"error": str(e)}, status=400)

    return Response(_serialize_offer(offer))