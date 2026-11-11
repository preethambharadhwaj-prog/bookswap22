from django.contrib import admin
from .models import Listing, Profile, Rating, TradeRequest

for m in (Profile, Listing, TradeRequest, Rating):
    admin.site.register(m)