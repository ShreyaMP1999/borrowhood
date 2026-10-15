from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from library.models import Category, Item


class Command(BaseCommand):
    help = "Create local demo accounts and listings; refuses to run with DEBUG off."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data is only allowed with DEBUG enabled.")
        owner, created = get_user_model().objects.get_or_create(
            username="maya", defaults={"email": "maya@example.test"}
        )
        if created:
            owner.set_password("BorrowhoodDemo!2026")
            owner.save()
        borrower, created = get_user_model().objects.get_or_create(
            username="alex", defaults={"email": "alex@example.test"}
        )
        if created:
            borrower.set_password("BorrowhoodDemo!2026")
            borrower.save()
        examples = [
            (
                "Tools",
                "Cordless drill kit",
                "Everything you need for a weekend project. Includes bits and two batteries.",
                "Maple Street",
            ),
            (
                "Outdoors",
                "Weekend camping tent",
                "Room for four, rain cover included. Please return dry and clean.",
                "Riverside",
            ),
            (
                "Photography",
                "Instant camera",
                "Capture the little moments. Bring your own film.",
                "Oak Avenue",
            ),
            (
                "Games",
                "Board game collection",
                "A cozy game night starts here. Five family favorites.",
                "Maple Street",
            ),
            (
                "Tools",
                "Garden starter set",
                "Trowel, gloves, rake and watering can for your next green project.",
                "Riverside",
            ),
            (
                "Outdoors",
                "Hiking backpack",
                "A comfortable 40L pack for a day on the trails.",
                "Oak Avenue",
            ),
        ]
        for name, title, description, location in examples:
            category, _ = Category.objects.get_or_create(name=name)
            Item.objects.get_or_create(
                title=title,
                owner=owner,
                defaults={
                    "category": category,
                    "description": description,
                    "location": location,
                },
            )
        self.stdout.write(
            self.style.SUCCESS("Demo ready: maya / alex, password BorrowhoodDemo!2026")
        )
