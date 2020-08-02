# Generated by Django 3.0.8 on 2020-07-31 21:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_auto_20200729_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='creator',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='creator', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='users',
            field=models.ManyToManyField(related_name='event_attendees', to=settings.AUTH_USER_MODEL),
        ),
    ]
