from django.contrib import admin
from .models import Candidate,Offer,Employee,OfferResponse

admin.site.register(Candidate)
admin.site.register(Offer)
admin.site.register(Employee)
admin.site.register(OfferResponse)

