from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
import pytz
# Create your models here.

DOCUMENTOS = (
    ("Cedula", "Cedula"),
    ("Pasaporte", "Pasaporte")
)


class Curso(models.Model):
    identificador = models.IntegerField(default=0000, null=False)
    nombre = models.CharField(max_length=300)
    monitores = models.ManyToManyField(User)

    def __str__(self):
        return self.nombre

class Clase(models.Model):
    inicio = models.DateTimeField(default=datetime.now)
    fin = models.DateTimeField(default=datetime.now)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    def __str__(self):
        return "Inicio: " + str(self.inicio.astimezone(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")) + " - Fin: " + str(self.fin.astimezone(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S"))

class Estudiante(models.Model):
    identificacion = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=30, choices=DOCUMENTOS)
    nombre = models.CharField(max_length=200)
    correo = models.CharField(max_length=100, unique=True)
    cursos = models.ManyToManyField(Curso, blank=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    monitor = models.BooleanField(default=False)

    def __str__(self):
        return self.identificacion + " - " + self.nombre

class Asistencia(models.Model):
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    monitor = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.estudiante.nombre + " - " + self.clase.curso.nombre + " - " + str(self.fecha.astimezone(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S"))