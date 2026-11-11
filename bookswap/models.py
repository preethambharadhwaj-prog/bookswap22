from django.conf import settings
from django.db import models
from django.db.models import Avg

User = settings.AUTH_USER_MODEL


class Level(models.TextChoices):
    POLY = "poly", "Polytechnic"
    BTECH = "btech", "B.E"
    MTECH = "mtech", "M.Tech"


DEPARTMENTS = [
    ("CSE", "Computer Science"), ("ISE", "Information Science"), ("AIML", "AI & Machine Learning"),
    ("ECE", "Electronics & Communication"), ("EEE", "Electrical & Electronics"),
    ("ME", "Mechanical"), ("CE", "Civil"), ("CHE", "Chemical"), ("BT", "Biotechnology"),
    ("OTH", "Other"),
]
YEARS = [(i, f"Year {i}") for i in range(1, 5)]
SEMESTERS = [(i, f"Sem {i}") for i in range(1, 9)]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=5, choices=Level.choices, blank=True)
    department = models.CharField(max_length=5, choices=DEPARTMENTS, blank=True)
    year = models.PositiveSmallIntegerField(choices=YEARS, null=True, blank=True)
    is_alumni = models.BooleanField(default=False)  # passed out; can still donate
    bio = models.TextField(blank=True)

    @property
    def avg_rating(self):
        return self.user.ratings_received.aggregate(a=Avg("score"))["a"]

    def __str__(self):
        return self.user.username


class Listing(models.Model):
    class Condition(models.TextChoices):
        NEW = "new", "Like new"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        WORN = "worn", "Worn"

    class Kind(models.TextChoices):
        BOOK = "book", "Textbook"
        NOTES = "notes", "Notes"

    class Offer(models.TextChoices):
        DONATE = "donate", "Donate"
        LEND = "lend", "Lend"
        TRADE = "trade", "Trade"

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=5, choices=Kind.choices, default=Kind.BOOK)
    offer = models.CharField(max_length=6, choices=Offer.choices, default=Offer.DONATE)
    level = models.CharField(max_length=5, choices=Level.choices)
    department = models.CharField(max_length=5, choices=DEPARTMENTS)
    year = models.PositiveSmallIntegerField(choices=YEARS)  # year the material is FOR
    semester = models.PositiveSmallIntegerField(choices=SEMESTERS)
    course_code = models.CharField(max_length=20, db_index=True)  # e.g. CS201
    edition = models.CharField(max_length=30, blank=True)
    condition = models.CharField(max_length=4, choices=Condition.choices)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.title} ({self.course_code})"


class TradeRequest(models.Model):
    class Type(models.TextChoices):  # mirrors Listing.Offer
        DONATE = "donate", "Claim"
        LEND = "lend", "Borrow"
        TRADE = "trade", "Trade"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        DONE = "done", "Completed"

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    kind = models.CharField(max_length=6, choices=Type.choices)
    offered = models.ForeignKey(  # your own listing, only for trades
        Listing, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    @property
    def owner(self):
        return self.listing.owner


class Rating(models.Model):
    trade = models.ForeignKey(TradeRequest, on_delete=models.CASCADE, related_name="ratings")
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_given")
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings_received")
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.CharField(max_length=300, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("trade", "rater")  # one rating per person per trade