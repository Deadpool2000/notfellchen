# Generated by Django 5.1.1 on 2024-11-14 18:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fellchensammlung', '0018_rescueorganization_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rescueorganization',
            old_name='comment',
            new_name='internal_comment',
        ),
    ]
