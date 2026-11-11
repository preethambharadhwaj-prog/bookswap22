from django.urls import path
from . import views

urlpatterns = [
    path("", views.listing_list, name="listing_list"),
    path("listings/new/", views.listing_create, name="listing_create"),
    path("listings/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("listings/<int:pk>/request/", views.request_create, name="request_create"),
    path("requests/", views.my_requests, name="my_requests"),
    path("requests/<int:pk>/rate/", views.rate, name="rate"),
    path("requests/<int:pk>/<str:action>/", views.request_update, name="request_update"),
    path("u/<str:username>/", views.profile, name="profile"),
    path("me/edit/", views.profile_edit, name="profile_edit"),
    path("signup/", views.signup, name="signup"),
]