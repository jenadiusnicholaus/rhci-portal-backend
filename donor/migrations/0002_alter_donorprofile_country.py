
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donorprofile',
            name='country',
            field=models.CharField(blank=True, db_column='country_id', max_length=100),
        ),
    ]
