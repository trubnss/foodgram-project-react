# Generated by Django 4.2.8 on 2024-02-05 12:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_remove_customuser_subscribers_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="is_subscribed",
        ),
    ]
