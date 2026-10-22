from django.db import migrations, models


def populate_pickup_location(apps, schema_editor):
    Resource = apps.get_model('resources', 'Resource')
    for resource in Resource.objects.select_related('provider').all():
        resource.pickup_address = resource.provider.address
        resource.pickup_latitude = resource.provider.latitude
        resource.pickup_longitude = resource.provider.longitude
        resource.save(update_fields=['pickup_address', 'pickup_latitude', 'pickup_longitude'])


class Migration(migrations.Migration):
    dependencies = [('resources', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='pickup_address',
            field=models.CharField(default='', max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='pickup_latitude',
            field=models.FloatField(default=6.773),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='pickup_longitude',
            field=models.FloatField(default=79.8816),
            preserve_default=False,
        ),
        migrations.RunPython(populate_pickup_location, migrations.RunPython.noop),
    ]
