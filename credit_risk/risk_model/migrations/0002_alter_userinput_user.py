# Generated by Django 5.1.5 on 2025-02-04 17:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("risk_model", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userinput",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_inputs",
                to="risk_model.customuser",
            ),
        ),
    ]
