from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Item, Booking

RESERVED = [Booking.Status.APPROVED, Booking.Status.COLLECTED]

@transaction.atomic
def transition(booking_id, actor, action, notes=""):
    # Every reservation change locks the same item first, serializing approvals.
    item_id = Booking.objects.values_list("item_id", flat=True).get(pk=booking_id)
    Item.objects.select_for_update().get(pk=item_id)
    booking = Booking.objects.select_for_update().select_related("item").get(pk=booking_id)
    owner = booking.item.owner_id == actor.id
    borrower = booking.borrower_id == actor.id
    rules = {
        "approve": (["pending"], "approved", owner),
        "decline": (["pending"], "declined", owner),
        "collect": (["approved"], "collected", owner),
        "return": (["collected"], "returned", owner),
        "cancel": (["pending", "approved"], "cancelled", borrower),
    }
    if action not in rules:
        raise ValidationError("Unknown booking action.")
    allowed, target, authorized = rules[action]
    if not authorized:
        raise PermissionDenied("You cannot perform this action.")
    if booking.status not in allowed:
        raise ValidationError("This action is unavailable for the current booking status.")
    if action == "approve":
        if not booking.item.active or booking.start_date < timezone.localdate():
            raise ValidationError("This listing is unavailable or the request has expired.")
        conflict = Booking.objects.filter(item_id=item_id, status__in=RESERVED, start_date__lte=booking.end_date, end_date__gte=booking.start_date).exclude(pk=booking.pk).exists()
        if conflict:
            raise ValidationError("These dates overlap an approved reservation.")
    if action == "collect" and booking.start_date > timezone.localdate():
        raise ValidationError("Collection is available from the booking start date.")
    booking.status = target
    if action == "return":
        if len(notes) > 1000:
            raise ValidationError("Return notes must be at most 1000 characters.")
        booking.return_notes = notes
    booking.save(update_fields=["status", "return_notes"])
    return booking
