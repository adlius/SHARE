# Generated by Django 3.2.5 on 2021-07-12 22:28

from django.db import migrations
from django.conf import settings


def ensure_share_system_user(apps, schema_editor):
    ShareUser = apps.get_model('share', 'ShareUser')
    Source = apps.get_model('share', 'Source')

    system_user = ShareUser.objects.filter(username=settings.APPLICATION_USERNAME).first()
    if system_user is None:
        system_user = user_manager.create_robot_user(
            username=settings.APPLICATION_USERNAME,
            robot='',
            is_trusted=True,
        )

    Source.objects.update_or_create(
        user=system_user,
        defaults={
            'name': settings.APPLICATION_USERNAME,
            'long_title': 'SHARE System',
            'canonical': True,
        }
    )


def ensure_share_admin_user(apps, schema_editor):
    import os
    ShareUser = apps.get_model('share', 'ShareUser')

    admin_username = 'admin'
    admin_user_exists = ShareUser.objects.filter(username=admin_username).exists()
    if not admin_user_exists:
        ShareUser.objects.create_superuser(
            admin_username,
            os.environ.get('SHARE_ADMIN_PASSWORD', 'password')
        )



class Migration(migrations.Migration):

    dependencies = [
        ('share', '0060_auto_20210712_1715'),
    ]

    operations = [
        migrations.RunPython(
            code=ensure_share_system_user,
        ),
        migrations.RunPython(
            code=ensure_share_admin_user,
        ),
    ]
