from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('resources', '0002_resource_pickup_location')]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='pickup_address',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='resource',
            name='pickup_latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='pickup_longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
