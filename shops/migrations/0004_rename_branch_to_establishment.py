import django.db.models.deletion
from django.db import migrations, models


def update_form_config_subtitle(apps, schema_editor):
    Barbershop = apps.get_model('shops', 'Barbershop')
    for shop in Barbershop.objects.all():
        cfg = dict(shop.booking_form_config or {})
        subtitle = cfg.get('subtitle') or ''
        if 'sucursal' in subtitle.lower():
            cfg['subtitle'] = (
                subtitle
                .replace('sucursal', 'establecimiento')
                .replace('Sucursal', 'Establecimiento')
            )
            shop.booking_form_config = cfg
            shop.save(update_fields=['booking_form_config'])


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0003_branch_open_close_time'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Branch',
            new_name='Establishment',
        ),
        migrations.AlterModelOptions(
            name='establishment',
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'establecimiento',
                'verbose_name_plural': 'establecimientos',
            },
        ),
        migrations.AlterField(
            model_name='establishment',
            name='shop',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='establishments',
                to='shops.barbershop',
            ),
        ),
        migrations.RenameField(
            model_name='barberprofile',
            old_name='branch',
            new_name='establishment',
        ),
        migrations.AlterField(
            model_name='barberprofile',
            name='establishment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='barbers',
                to='shops.establishment',
                verbose_name='establecimiento',
            ),
        ),
        migrations.RunPython(update_form_config_subtitle, migrations.RunPython.noop),
    ]
