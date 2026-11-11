from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DEPARTMENTS, YEARS, Level, Listing, Profile, Rating, TradeRequest


class SignupForm(UserCreationForm):
    level = forms.ChoiceField(choices=Level.choices)
    department = forms.ChoiceField(choices=DEPARTMENTS)
    year = forms.ChoiceField(choices=YEARS)
    is_alumni = forms.BooleanField(required=False, label="I have already passed out")

    class Meta:
        model = User
        fields = ("username", "email")

    def save_profile(self, user):
        d = self.cleaned_data
        return Profile.objects.create(user=user, level=d["level"], department=d["department"],
                                      year=d["year"], is_alumni=d["is_alumni"])


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["level", "department", "year", "is_alumni", "bio"]


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "kind", "offer", "level", "department", "year", "semester",
                  "course_code", "edition", "condition", "description"]


class TradeRequestForm(forms.ModelForm):
    class Meta:
        model = TradeRequest
        fields = ["offered", "message"]  # kind is copied from the listing's offer

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offered"].queryset = Listing.objects.filter(owner=user, is_available=True)
        self.fields["offered"].required = False
        self.fields["offered"].label = "Your item to swap (trades only)"


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["score", "comment"]