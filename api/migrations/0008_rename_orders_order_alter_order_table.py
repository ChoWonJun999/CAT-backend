# Generated by Django 5.1 on 2024-10-17 06:21

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0007_rename_oders_orders_alter_orders_table"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Orders",
            new_name="Order",
        ),
        migrations.AlterModelTable(
            name="order",
            table="order",
        ),
    ]
