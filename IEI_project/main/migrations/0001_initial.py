# Generated by Django 5.1.3 on 2024-11-15 09:06

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Localidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Provincia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Monumento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('tipo', models.CharField(choices=[('YA', 'Yacimiento_arqueológico'), ('IE', 'Iglesia-Ermita'), ('MC', 'Monasterio-Convento'), ('CFT', 'Castillo-Fortaleza-Torre'), ('ES', 'Edificio singular'), ('PU', 'Puente'), ('OT', 'Otros')], max_length=3)),
                ('direccion', models.CharField(max_length=255)),
                ('codigo_postal', models.CharField(help_text='Ingrese un código postal de 5 dígitos', max_length=5, validators=[django.core.validators.MinLengthValidator(5), django.core.validators.RegexValidator(message='El código postal debe tener exactamente 5 dígitos', regex='^\\d{5}$')])),
                ('longitud', models.DecimalField(decimal_places=6, max_digits=9)),
                ('latitud', models.DecimalField(decimal_places=6, max_digits=9)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('en_localidad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monumentos', to='main.localidad')),
            ],
        ),
        migrations.AddField(
            model_name='localidad',
            name='en_provincia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='localidades', to='main.provincia'),
        ),
    ]