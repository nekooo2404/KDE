from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LocationTerm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.CharField(max_length=255, unique=True)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("density", models.FloatField(default=0.5)),
                ("city", models.CharField(max_length=50)),
            ],
        ),
    ]
