from datetime import time

from django.db import migrations, models


DEFAULT_OPEN = time(9, 0)
DEFAULT_CLOSE = time(20, 0)


def copy_hours_to_branches(apps, schema_editor):
    Barbershop = apps.get_model('shops', 'Barbershop')
    Branch = apps.get_model('shops', 'Branch')
    for shop in Barbershop.objects.all():
        open_time = getattr(shop, 'open_time', None) or DEFAULT_OPEN
        close_time = getattr(shop, 'close_time', None) or DEFAULT_CLOSE
        Branch.objects.filter(shop=shop).update(open_time=open_time, close_time=close_time)


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0002_add_open_close_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='close_time',
            field=models.TimeField(default=DEFAULT_CLOSE, verbose_name='cierra a'),
        ),
        migrations.AddField(
            model_name='branch',
            name='open_time',
            field=models.TimeField(default=DEFAULT_OPEN, verbose_name='abre a'),
        ),
        migrations.RunPython(copy_hours_to_branches, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='barbershop',
            name='close_time',
        ),
        migrations.RemoveField(
            model_name='barbershop',
            name='open_time',
        ),
    ]
