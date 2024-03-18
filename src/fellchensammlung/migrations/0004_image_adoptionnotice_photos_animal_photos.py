# Generated by Django 5.0.3 on 2024-03-18 16:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fellchensammlung', '0003_markdowncontent'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image', models.ImageField(upload_to='images')),
                ('alt_text', models.TextField(max_length=2000)),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='adoptionnotice',
            name='photos',
            field=models.ManyToManyField(blank=True, to='fellchensammlung.image'),
        ),
        migrations.AddField(
            model_name='animal',
            name='photos',
            field=models.ManyToManyField(blank=True, to='fellchensammlung.image'),
        ),
    ]
