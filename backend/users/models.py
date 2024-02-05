from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from api.constants import USER_MODEL_MAX_LENGTH


class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=USER_MODEL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        max_length=USER_MODEL_MAX_LENGTH,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=USER_MODEL_MAX_LENGTH,
        verbose_name="Фамилия",
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        CustomUser,
        related_name="following",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    subscribed_to = models.ForeignKey(
        CustomUser,
        related_name="followers",
        on_delete=models.CASCADE,
        verbose_name="На кого подписан",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            UniqueConstraint(
                fields=["subscriber", "subscribed_to"],
                name="unique_subscription",
            ),
            CheckConstraint(
                check=~Q(subscriber=F("subscribed_to")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return (
            f"{self.subscriber.username}"
            f" подписан на {self.subscribed_to.username}"
        )
