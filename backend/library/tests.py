from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.db import connection, connections, close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from .models import Category, Item, Booking
from .services import transition


class LendingTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            "owner", password="OwnerStrong!42"
        )
        self.borrower = get_user_model().objects.create_user(
            "borrower", password="BorrowerStrong!42"
        )
        self.other = get_user_model().objects.create_user(
            "other", password="OtherStrong!42"
        )
        self.category = Category.objects.create(name="Tools")
        self.item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title="Drill",
            description="With bits",
            location="Riverside",
        )
        self.today = timezone.localdate()
        self.client.force_authenticate(self.borrower)

    def booking(self, **kwargs):
        values = dict(
            item=self.item,
            borrower=self.borrower,
            start_date=self.today,
            end_date=self.today + timedelta(days=2),
        )
        values.update(kwargs)
        return Booking.objects.create(**values)

    def request(self, **kwargs):
        data = {
            "item": self.item.pk,
            "start_date": str(self.today),
            "end_date": str(self.today + timedelta(days=2)),
        }
        data.update(kwargs)
        return self.client.post("/api/bookings/", data)

    def change(self, booking, action):
        return self.client.post(
            f"/api/bookings/{booking.pk}/transition/", {"action": action}, format="json"
        )

    def test_registration_and_logout_revoke_token(self):
        self.client.force_authenticate(None)
        result = self.client.post(
            "/api/auth/register/",
            {
                "username": "newneighbor",
                "email": "neighbor@example.test",
                "password": "UniqueLongPass!42",
            },
        )
        self.assertEqual(result.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + result.data["token"])
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/me/").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_weak_password_rejected(self):
        self.assertEqual(
            self.client.post(
                "/api/auth/register/",
                {"username": "new", "email": "n@example.test", "password": "123"},
            ).status_code,
            400,
        )

    def test_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post(
                "/api/auth/login/", {"username": "owner", "password": "wrong"}
            ).status_code,
            400,
        )
        self.assertIn(
            "token",
            self.client.post(
                "/api/auth/login/", {"username": "owner", "password": "OwnerStrong!42"}
            ).data,
        )

    def test_anonymous_can_browse_but_not_create(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/items/").status_code, 200)
        self.assertEqual(self.request().status_code, 401)

    def test_search_and_category_filter(self):
        self.assertEqual(
            self.client.get("/api/items/?search=riverside").data["count"], 1
        )
        self.assertEqual(self.client.get("/api/items/?search=tent").data["count"], 0)
        self.assertEqual(self.client.get("/api/items/?category=bad").data["count"], 0)

    def test_listing_owner_cannot_be_spoofed(self):
        result = self.client.post(
            "/api/items/",
            {
                "title": "Saw",
                "description": "Hand saw",
                "category": self.category.pk,
                "location": "Park",
                "owner": self.owner.pk,
            },
        )
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["owner"], self.borrower.pk)

    def test_only_owner_can_edit(self):
        self.assertEqual(
            self.client.patch(
                f"/api/items/{self.item.pk}/", {"title": "Stolen"}
            ).status_code,
            403,
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.patch(
                f"/api/items/{self.item.pk}/", {"active": False}
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/items/").data["count"], 0)
        self.assertEqual(
            self.client.patch(
                f"/api/items/{self.item.pk}/?mine=1", {"active": True}
            ).status_code,
            200,
        )

    def test_self_borrow_disallowed(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.request().status_code, 400)

    def test_past_and_reversed_dates_rejected(self):
        self.assertEqual(
            self.request(start_date=str(self.today - timedelta(days=1))).status_code,
            400,
        )
        self.assertEqual(
            self.request(end_date=str(self.today - timedelta(days=1))).status_code, 400
        )

    def test_inactive_item_cannot_be_borrowed(self):
        self.item.active = False
        self.item.save()
        self.assertEqual(self.request().status_code, 400)

    def test_cannot_forge_approved_status(self):
        result = self.request(status="approved", borrower=self.other.pk)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["status"], "pending")
        self.assertEqual(result.data["borrower"], self.borrower.pk)

    def test_booking_privacy(self):
        booking = self.booking()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/bookings/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/bookings/{booking.pk}/").status_code, 404
        )

    def test_borrower_cannot_approve(self):
        self.assertEqual(self.change(self.booking(), "approve").status_code, 403)

    def test_overlapping_approvals_rejected_including_end_day(self):
        self.booking(status="approved")
        conflict = self.booking(start_date=self.today + timedelta(days=2))
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change(conflict, "approve").status_code, 400)

    def test_non_overlapping_approval_allowed(self):
        self.booking(status="approved")
        later = self.booking(
            start_date=self.today + timedelta(days=3),
            end_date=self.today + timedelta(days=4),
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change(later, "approve").status_code, 200)

    def test_cancellation_releases_reservation(self):
        first = self.booking(status="approved")
        self.assertEqual(self.change(first, "cancel").status_code, 200)
        second = self.booking()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change(second, "approve").status_code, 200)

    def test_complete_lifecycle_and_review(self):
        booking = self.booking()
        self.client.force_authenticate(self.owner)
        for action in ["approve", "collect", "return"]:
            self.assertEqual(self.change(booking, action).status_code, 200)
        self.client.force_authenticate(self.borrower)
        response = self.client.post(
            "/api/reviews/", {"booking": booking.pk, "rating": 5, "comment": "Perfect!"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.client.post(
                "/api/reviews/", {"booking": booking.pk, "rating": 4}
            ).status_code,
            400,
        )

    def test_review_requires_return_and_borrower(self):
        booking = self.booking()
        self.assertEqual(
            self.client.post(
                "/api/reviews/", {"booking": booking.pk, "rating": 5}
            ).status_code,
            400,
        )
        booking.status = "returned"
        booking.save()
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.post(
                "/api/reviews/", {"booking": booking.pk, "rating": 5}
            ).status_code,
            400,
        )

    def test_invalid_rating(self):
        booking = self.booking(status="returned")
        self.assertEqual(
            self.client.post(
                "/api/reviews/", {"booking": booking.pk, "rating": 6}
            ).status_code,
            400,
        )

    def test_invalid_transition(self):
        self.client.force_authenticate(self.owner)
        booking = self.booking()
        self.assertEqual(self.change(booking, "return").status_code, 400)
        self.assertEqual(self.change(booking, ["approve"]).status_code, 400)

    def test_early_collection_rejected(self):
        booking = self.booking(
            status="approved", start_date=self.today + timedelta(days=1)
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change(booking, "collect").status_code, 400)

    def test_expired_request_cannot_be_approved(self):
        booking = self.booking(start_date=self.today - timedelta(days=1))
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change(booking, "approve").status_code, 400)

    def test_dashboard_and_overdue(self):
        self.booking(
            status="collected",
            start_date=self.today - timedelta(days=3),
            end_date=self.today - timedelta(days=1),
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get("/api/dashboard/").data["overdue"], 1)
        self.assertEqual(self.client.get("/api/dashboard/").data["items_shared"], 1)


@skipUnless(
    connection.vendor == "postgresql", "Row-lock concurrency requires PostgreSQL"
)
class ConcurrentApprovalTests(TransactionTestCase):
    def test_only_one_simultaneous_approval_succeeds(self):
        owner = get_user_model().objects.create_user("owner")
        borrower = get_user_model().objects.create_user("borrower")
        category = Category.objects.create(name="Tools")
        item = Item.objects.create(
            owner=owner,
            category=category,
            title="Drill",
            description="Drill",
            location="Park",
        )
        bookings = [
            Booking.objects.create(
                item=item,
                borrower=borrower,
                start_date=timezone.localdate(),
                end_date=timezone.localdate(),
            )
            for _ in range(2)
        ]
        barrier = Barrier(2)

        def approve(pk):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                transition(pk, owner, "approve")
                return True
            except ValidationError:
                return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(approve, [b.pk for b in bookings]))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(Booking.objects.filter(status="approved").count(), 1)
