from django.urls import path
from .views import get_context
from .views_offers import (
    create_offer_view,
    send_offer_view,
    accept_offer_view,
    discuss_offer_view,
    reject_offer_view,
)

urlpatterns = [
    path("context/", get_context, name="get_context"),

    path("offers/create/", create_offer_view, name="create_offer"),
    path("offers/<int:offer_id>/send/", send_offer_view, name="send_offer"),
    path("offers/<int:offer_id>/accept/", accept_offer_view, name="accept_offer"),
    path("offers/<int:offer_id>/discuss/", discuss_offer_view, name="discuss_offer"),
    path("offers/<int:offer_id>/reject/", reject_offer_view, name="reject_offer"),
]