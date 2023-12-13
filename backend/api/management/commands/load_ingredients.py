import csv
import os

from api.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load data for Ingredient model from CSV file"

    def handle(self, *args, **options):
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ingredients.csv"
        )
        with open(file_path, "r") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                name = row[0]
                measurement_unit = row[1]
                Ingredient.objects.create(
                    name=name, measurement_unit=measurement_unit)

        self.stdout.write(self.style.SUCCESS("Data loaded successfully"))
