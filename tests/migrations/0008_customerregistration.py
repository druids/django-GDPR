# Generated by Django 3.1 on 2021-04-16 11:47

from django.db import migrations, models
import gdpr.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0007_childe_extraparentd_parentb_parentc_topparenta'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_address', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(gdpr.mixins.AnonymizationModelMixin, models.Model),
        ),
    ]
