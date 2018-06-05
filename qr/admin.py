
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

# Register your models here.
from .models import *


@admin.register(Estudiante)
class EstudianteAdmin(ImportExportModelAdmin):
    pass


admin.site.register(Clase)
admin.site.register(Curso)
#admin.site.register(Estudiante)
admin.site.register(Asistencia)