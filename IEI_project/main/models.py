from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator

class Provincia(models.Model):
    nombre = models.CharField(max_length=255, )

    def __str__(self):
        return self.nombre
    

class Localidad(models.Model):
    nombre = models.CharField(max_length=255)
    en_provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name="localidades")

    def __str__(self):
        return self.nombre

class Tipo(models.TextChoices):
    YACIMIENTO_ARQUEOLOGICO = "YA", 'Yacimiento_arqueológico'
    IGLESIA_ERMITA = "IE", 'Iglesia-Ermita'
    MONASTERIO_CONVENTO = "MC", 'Monasterio-Convento'
    CASTILLO_FORTALEZA_TORRE = "CFT", 'Castillo-Fortaleza-Torre'
    EDIFICIO_SINGULAR = "ES", 'Edificio singular'
    PUENTE = "PU", 'Puente'
    OTROS = "OT", 'Otros'

class Monumento(models.Model):
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    direccion = models.CharField(max_length=255)
    codigo_postal = models.CharField(
        max_length=5,
        validators=[
            MinLengthValidator(5),
            RegexValidator(regex='^\d{5}$', message='El código postal debe tener exactamente 5 dígitos')
        ],
        help_text='Ingrese un código postal de 5 dígitos'
        )
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    descripcion = models.TextField(blank=True, null=True)
    en_localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE, related_name="monumentos")

    def __str__(self):
        return self.nombre
