from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_profile_name_address_split'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='email',
        ),
    ]

