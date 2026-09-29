from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
        ('shops', '0004_rename_branch_to_establishment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='branch',
            new_name='establishment',
        ),
        migrations.AlterField(
            model_name='appointment',
            name='establishment',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='appointments',
                to='shops.establishment',
                verbose_name='establecimiento',
            ),
        ),
    ]
