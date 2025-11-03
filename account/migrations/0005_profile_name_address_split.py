from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_profile_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='title',
            field=models.CharField(blank=True, choices=[('นาย', 'นาย'), ('นาง', 'นาง'), ('นางสาว', 'นางสาว'), ('อื่นๆ', 'อื่นๆ')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='house_no',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='profile',
            name='moo',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='profile',
            name='street',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='subdistrict',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='district',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='province',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='profile',
            name='gender',
            field=models.CharField(blank=True, choices=[('ชาย', 'ชาย'), ('หญิง', 'หญิง'), ('อื่นๆ', 'อื่นๆ')], max_length=10),
        ),
        migrations.RemoveField(
            model_name='profile',
            name='address',
        ),
    ]

