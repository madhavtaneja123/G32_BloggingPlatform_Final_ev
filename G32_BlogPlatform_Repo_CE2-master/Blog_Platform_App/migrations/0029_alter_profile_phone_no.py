# Generated by Django 5.2 on 2025-04-16 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Blog_Platform_App', '0028_remove_comment_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='phone_no',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
