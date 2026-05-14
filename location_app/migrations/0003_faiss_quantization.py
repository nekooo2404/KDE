from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location_app', '0002_semantic_embeddings'),
    ]

    operations = [
        migrations.AddField(
            model_name='semanticlocation',
            name='embedding_min',
            field=models.TextField(default='null', help_text='JSON array of per-dimension min values (for int8 dequantization)'),
        ),
        migrations.AddField(
            model_name='semanticlocation',
            name='embedding_max',
            field=models.TextField(default='null', help_text='JSON array of per-dimension max values (for int8 dequantization)'),
        ),
    ]
