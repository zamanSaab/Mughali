# Generated by Django 4.2.13 on 2024-05-27 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0003_ordermeal_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'In progress'), (2, 'Out for delivery'), (3, 'Delivered'), (4, 'Paid')], default=0),
        ),
        migrations.AlterField(
            model_name='ordermeal',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
