import os
import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

file_path = os.path.join(BASE_DIR, "data", "ingredients.csv")


class Command(BaseCommand):
    help = "Загрузка ингредиентов из CSV файла в базу данных."

    def handle(self, *args, **options):
        with open("data/ingredients.csv", "r") as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                name = row[0].strip()
                measurement_unit = row[1].strip()
                Ingredient.objects.create(
                    name=name, measurement_unit=measurement_unit
                )

        self.stdout.write(
            self.style.SUCCESS("Ингредиенты успешно загружены из CSV")
        )
