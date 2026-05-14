# Generated migration for SemanticLocation and LocationQuery models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SemanticLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_label', models.CharField(db_index=True, max_length=100, unique=True)),
                ('city_name', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('population', models.IntegerField(default=0)),
                ('embedding_json', models.TextField(help_text='JSON serialized embedding vector')),
                ('landmarks', models.JSONField(default=list, help_text='List of landmark/cultural references')),
                ('coverage_score', models.FloatField(default=0.5, help_text='How well this location covers semantic space (0..1)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'location_semantic',
                'ordering': ['-population'],
            },
        ),
        migrations.CreateModel(
            name='LocationQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_text', models.TextField()),
                ('inferred_city', models.CharField(blank=True, max_length=100, null=True)),
                ('inferred_lat', models.FloatField(blank=True, null=True)),
                ('inferred_lon', models.FloatField(blank=True, null=True)),
                ('confidence', models.FloatField(blank=True, null=True)),
                ('method', models.CharField(choices=[('semantic', 'Semantic Embeddings'), ('tfidf', 'TF-IDF Similarity'), ('llm', 'LLM-based (Gemini)')], default='semantic', max_length=20)),
                ('keywords_extracted', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'location_query',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='semanticlocation',
            index=models.Index(fields=['city_label'], name='location_se_city_la_idx'),
        ),
        migrations.AddIndex(
            model_name='semanticlocation',
            index=models.Index(fields=['-population'], name='location_se_populat_idx'),
        ),
        migrations.AddIndex(
            model_name='locationquery',
            index=models.Index(fields=['method', '-created_at'], name='location_qu_method_idx'),
        ),
    ]
