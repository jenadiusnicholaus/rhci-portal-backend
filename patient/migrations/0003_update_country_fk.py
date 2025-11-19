# Manual migration - Safe for production
# This migration only updates the model definition, doesn't change DB schema

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0007_countrylookup'),
        ('patient', '0002_patientprofile_photo'),
    ]

    operations = [
        # This operation tells Django the field definition changed
        # but since db_column='country_fk_id' matches the existing column,
        # no actual SQL will be executed
        migrations.AlterField(
            model_name='patientprofile',
            name='country_fk',
            field=models.ForeignKey(
                blank=True, 
                db_column='country_fk_id', 
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='patients', 
                to='auth_app.countrylookup'
            ),
        ),
    ]
