# Generated by Django 5.0.3 on 2024-03-18 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fellchensammlung', '0002_remove_animal_adoption_notice_adoptionnotice_animals'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkdownContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Markdown content',
            },
        ),
    ]
