from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    first_name = models.CharField(
        max_length=50,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name="Фамилия",
    )
    email = models.EmailField(unique=True)
    subscribers = models.ManyToManyField(
        "self", symmetrical=False, blank=True
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
