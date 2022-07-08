# Generated by Django 3.2.4 on 2022-06-23 09:50

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0005_auto_20220623_1641'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='likers',
            field=models.ManyToManyField(blank=True, related_name='likers', to=settings.AUTH_USER_MODEL),
        ),
    ]