# Generated by Django 5.1.7 on 2025-05-04 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Blog_Platform_App', '0031_alter_profile_bio_alter_profile_facebook_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='flask_blog_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
