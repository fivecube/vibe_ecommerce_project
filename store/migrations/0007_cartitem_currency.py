# Generated by Django 5.2.3 on 2025-06-22 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_alter_cartitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='currency',
            field=models.CharField(default='USD', help_text='Currency code, e.g. USD, EUR', max_length=8),
        ),
    ]
