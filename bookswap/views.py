from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ListingForm, ProfileForm, RatingForm, SignupForm, TradeRequestForm
from .models import DEPARTMENTS, SEMESTERS, YEARS, Level, Listing, Profile, Rating, TradeRequest


def signup(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        form.save_profile(user)
        login(request, user)
        return redirect("listing_list")
    return render(request, "registration/signup.html", {"form": form})


FILTERS = ("level", "department", "year", "semester", "course_code", "edition", "condition")


def listing_list(request):
    g = request.GET.dict()
    # first visit: default to what this student needs (their own level/dept/year)
    if not g and request.user.is_authenticated and hasattr(request.user, "profile"):
        p = request.user.profile
        g = {"level": p.level, "department": p.department, "year": p.year or ""}
    qs = Listing.objects.filter(is_available=True).select_related("owner__profile")
    if g.get("q"):
        qs = qs.filter(Q(title__icontains=g["q"]) | Q(description__icontains=g["q"]))
    for f in FILTERS:
        if g.get(f):
            qs = qs.filter(**{f"{f}__iexact": g[f]})
    return render(request, "bookswap/listing_list.html", {
        "listings": qs, "g": g, "levels": Level.choices, "departments": DEPARTMENTS, "years": YEARS,
        "semesters": SEMESTERS, "conditions": Listing.Condition.choices})


def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    form = TradeRequestForm(user=request.user) if request.user.is_authenticated else None
    return render(request, "bookswap/listing_detail.html", {"listing": listing, "form": form})


@login_required
def listing_create(request):
    form = ListingForm(request.POST or None)
    if form.is_valid():
        listing = form.save(commit=False)
        listing.owner = request.user
        listing.save()
        return redirect(listing_detail, pk=listing.pk)
    return render(request, "bookswap/listing_form.html", {"form": form})


@login_required
@require_POST
def request_create(request, pk):
    listing = get_object_or_404(Listing, pk=pk, is_available=True)
    if listing.owner == request.user:
        return HttpResponseForbidden("This is your own listing.")
    form = TradeRequestForm(request.POST, user=request.user)
    if form.is_valid():
        tr = form.save(commit=False)
        tr.listing, tr.requester, tr.kind = listing, request.user, listing.offer
        tr.save()
    return redirect("my_requests")


@login_required
def my_requests(request):
    return render(request, "bookswap/my_requests.html", {
        "incoming": TradeRequest.objects.filter(listing__owner=request.user),
        "outgoing": TradeRequest.objects.filter(requester=request.user),
    })


@login_required
@require_POST
def request_update(request, pk, action):
    tr = get_object_or_404(TradeRequest, pk=pk, listing__owner=request.user)
    if action == "accept":
        tr.status = "accepted"
        tr.listing.is_available = False  # hide from search while deal is on
        tr.listing.save()
    elif action == "decline":
        tr.status = "declined"
    elif action == "done" and tr.status == "accepted":
        tr.status = "done"
    tr.save()
    return redirect("my_requests")


@login_required
def rate(request, pk):
    tr = get_object_or_404(TradeRequest, pk=pk, status="done")
    if request.user not in (tr.requester, tr.owner):
        return HttpResponseForbidden()
    ratee = tr.owner if request.user == tr.requester else tr.requester
    form = RatingForm(request.POST or None)
    if form.is_valid() and not tr.ratings.filter(rater=request.user).exists():
        r = form.save(commit=False)
        r.trade, r.rater, r.ratee = tr, request.user, ratee
        r.save()
        return redirect("profile", username=ratee.username)
    return render(request, "bookswap/rating_form.html", {"form": form, "ratee": ratee})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    prof, _ = Profile.objects.get_or_create(user=user)
    return render(request, "bookswap/profile.html", {
        "u": user, "prof": prof,
        "listings": user.listings.filter(is_available=True),
        "ratings": user.ratings_received.select_related("rater"),
    })


@login_required
def profile_edit(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=prof)
    if form.is_valid():
        form.save()
        return redirect("profile", username=request.user.username)
    return render(request, "bookswap/listing_form.html", {"form": form})